"""The collectors in labkit.runner, against a stubbed message stream.

This is the one part of labkit you cannot check by reading, and the one part that
costs money to check for real, so it is checked here instead.
"""

import asyncio

import pytest

import labkit
from labkit.runner import AgentRunner, ResultMessage, options


class Block:
    def __init__(self, name=None, input=None, text=None):
        self.name, self.input, self.text = name, input, text


def tool_block(name, **input):
    return labkit.runner.ToolUseBlock(id=f"tu_{name}", name=name, input=input)


def assistant(blocks, message_id="m1", parent=None):
    return labkit.runner.AssistantMessage(
        content=blocks, model="test", message_id=message_id, parent_tool_use_id=parent
    )


def result(*, cost=0.01, turns=3, denials=None, subtype="success",
           text="done", structured=None):
    return ResultMessage(
        subtype=subtype, duration_ms=2500, duration_api_ms=2000, is_error=False,
        num_turns=turns, session_id="s", total_cost_usd=cost, result=text,
        permission_denials=denials or [], structured_output=structured,
    )


def drive(runner, messages):
    """Run `ask()` with the SDK's query() replaced by a fixed list of messages."""
    async def fake_query(*, prompt, options):
        for message in messages:
            yield message

    original = labkit.runner.query
    labkit.runner.query = fake_query
    try:
        return asyncio.run(runner.ask("anything"))
    finally:
        labkit.runner.query = original


def test_tool_calls_are_collected_in_order_and_toolsearch_is_skipped():
    runner = AgentRunner(options(model="m"))
    run = drive(runner, [
        assistant([tool_block("ToolSearch", query="x"),
                   tool_block("Grep", pattern="charge"),
                   tool_block("Read", file_path="a.py")]),
        result(),
    ])
    assert run.names == ["Grep", "Read"], "ToolSearch is plumbing, not a choice"


def test_names_are_uncollapsed_so_counting_works():
    runner = AgentRunner(options(model="m"))
    run = drive(runner, [
        assistant([tool_block("Grep"), tool_block("Grep"), tool_block("Read")]),
        result(),
    ])
    assert run.names.count("Grep") == 2
    assert labkit.collapse(run.names) == ["Grep x2", "Read"]


def test_strip_shortens_names_but_keeps_the_wire_name():
    runner = AgentRunner(options(model="m"), strip="mcp__support__")
    run = drive(runner, [assistant([tool_block("mcp__support__get_customer")]), result()])
    assert run.names == ["get_customer"]
    assert run.calls[0].name == "mcp__support__get_customer"


def test_response_and_subagent_attribution_survive():
    """Lab 2's parallelism lesson depends on both of these fields."""
    runner = AgentRunner(options(model="m"))
    run = drive(runner, [
        assistant([tool_block("Agent", subagent_type="web_searcher"),
                   tool_block("Agent", subagent_type="document_searcher")], message_id="r1"),
        assistant([tool_block("search_web", query="music")], message_id="r2", parent="tu_a"),
        result(),
    ])
    together = run.by_response(only=["Agent"])
    assert len(together) == 1, "both spawns arrived in one response, so they ran together"
    assert len(next(iter(together.values()))) == 2
    assert list(run.by_subagent()) == ["tu_a"]


def test_executed_is_attempted_minus_denied_one_for_one():
    runner = AgentRunner(options(model="m"), strip="mcp__support__")
    denied = {"tool_name": "mcp__support__process_refund",
              "tool_input": {"amount": 650.0, "order_id": "ORD-0021"}}
    run = drive(runner, [
        assistant([
            tool_block("mcp__support__process_refund", amount=650.0, order_id="ORD-0021"),
            tool_block("mcp__support__process_refund", amount=89.99, order_id="ORD-0003"),
        ]),
        result(denials=[denied]),
    ])
    amounts = [call["amount"] for call in run.executed("process_refund")]
    assert amounts == [89.99], "the denied 650 was attempted but never ran"
    assert run.used("process_refund") is True


def test_cost_turns_and_structured_output_are_carried():
    runner = AgentRunner(options(model="m"))
    run = drive(runner, [assistant([Block(text="hi")]),
                         result(cost=0.0412, turns=6, structured={"topic": "t"})])
    assert run.cost == pytest.approx(0.0412)
    assert run.turns == 6
    assert run.duration_s == pytest.approx(2.5)
    assert run.structured_output == {"topic": "t"}
    assert run.reply == "done"
    assert runner.total == pytest.approx(0.0412)


def test_both_sides_of_every_turn_are_kept():
    """The transcript panel pairs them, so a missing half would silently misalign it."""
    runner = AgentRunner(options(model="m"))
    run = drive(runner, [assistant([Block(text="thinking")]), result(text="the answer")])
    assert run.prompts == ["anything"]
    assert run.replies == ["the answer"], "one entry per turn, not per text block"
    assert run.reply == "the answer"


def test_spend_accumulates_across_runs():
    runner = AgentRunner(options(model="m"))
    drive(runner, [result(cost=0.01)])
    drive(runner, [result(cost=0.02)])
    assert runner.spend == [0.01, 0.02]
    assert runner.total == pytest.approx(0.03)


def test_before_runs_ahead_of_every_call():
    fired = []
    runner = AgentRunner(options(model="m"), before=lambda: fired.append(1))
    drive(runner, [result()])
    drive(runner, [result()])
    assert fired == [1, 1], "fixtures must be re-armed on every run, not just the first"


def test_overrides_reach_the_options_without_mutating_the_runner():
    runner = AgentRunner(options(model="m", tools=["Grep"]))
    replaced = runner._options({"tools": ["Read"], "permission_mode": "dontAsk"})
    assert replaced.tools == ["Read"] and replaced.permission_mode == "dontAsk"
    assert runner.options.tools == ["Grep"], "the runner's own options are untouched"
    assert replaced.setting_sources == [] and replaced.env == labkit.NO_CONNECTORS


def test_options_carries_the_two_invariants_and_lets_them_be_overridden():
    assert options(model="m").setting_sources == []
    assert options(model="m").env == labkit.NO_CONNECTORS
    assert options(model="m", setting_sources=["project"]).setting_sources == ["project"]
