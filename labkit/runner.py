"""One run of an agent, and what came back from it.

Every Agent SDK lab wrote its own version of this: drive `query()`, collect the tool
calls as they arrive, keep the final text, keep the cost. The differences between
those versions were accidents rather than lessons, so there is one of them here.

What is *not* hidden is the configuration. `ClaudeAgentOptions` is built in the
notebook, in full, because which tools exist, which are approved and what the
permission mode is are the things these labs are about.
"""

from __future__ import annotations

import dataclasses
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Sequence

from claude_agent_sdk import (
    AssistantMessage, ClaudeAgentOptions, ClaudeSDKClient, ResultError, ResultMessage,
    ToolUseBlock, query,
)

__all__ = ["NO_CONNECTORS", "options", "AgentRunner", "Run", "Call"]

# A claude.ai login carries your organisation's connectors into the session, and
# setting_sources=[] does not exclude them: a connector is not a filesystem setting.
# Left on, a student signed in to a subscription gets MCP tools the lab never defined,
# in the middle of a lab about which tool the agent reaches for. A key does not load
# them, and neither does a setup-token, so this is the one line that makes a run the
# same on every credential.
NO_CONNECTORS = {"ENABLE_CLAUDEAI_MCP_SERVERS": "false"}


def options(**settings) -> ClaudeAgentOptions:
    """`ClaudeAgentOptions`, plus the two settings that are the same in every lab.

    `setting_sources=[]` loads nothing from disk: no CLAUDE.md, no project settings,
    nothing from your own machine. Everything the agent has comes from the cell.
    """
    settings.setdefault("setting_sources", [])
    settings.setdefault("env", NO_CONNECTORS)
    return ClaudeAgentOptions(**settings)


@dataclass(frozen=True)
class Call:
    """One tool call the model made."""

    name: str                              # as the stream reports it, mcp__server__tool
    input: dict
    short: str                             # with the runner's server prefix removed
    message_id: str | None = None          # which response it arrived in
    parent_tool_use_id: str | None = None  # set when it came from inside a subagent


@dataclass
class Run:
    """What one run produced."""

    calls: list[Call] = field(default_factory=list)
    reply: str = ""
    cost: float = 0.0
    turns: int = 0
    duration_s: float = 0.0
    denials: list = field(default_factory=list)
    endings: list = field(default_factory=list)
    structured_output: Any = None
    result: ResultMessage | None = None    # the SDK object itself, never hidden

    @property
    def names(self) -> list[str]:
        """Tool names in order, uncollapsed, so counting them is meaningful."""
        return [call.short for call in self.calls]

    def used(self, tool: str) -> bool:
        return any(name.endswith(tool) for name in self.names)

    def executed(self, tool: str) -> list[dict]:
        """The calls that actually ran.

        A denied call is still in `calls`, because the model made it; the hook stopped
        it happening. Attempted minus denied is what moved money.
        """
        import json

        denied = [
            (denial.get("tool_name"),
             json.dumps(denial.get("tool_input"), sort_keys=True, default=str))
            for denial in self.denials
        ]
        ran = []
        for call in self.calls:
            if not call.name.endswith(tool):
                continue
            key = (call.name, json.dumps(call.input, sort_keys=True, default=str))
            if key in denied:
                denied.remove(key)                 # one denial cancels one attempt
                continue
            ran.append(call.input)
        return ran

    def by_response(self, only: Sequence[str] = ()) -> dict[str, list[Call]]:
        """Calls grouped by the response they arrived in.

        Several tool calls in a single response run at the same time, so this is how
        you tell parallel work from sequential work.
        """
        grouped: dict[str, list[Call]] = defaultdict(list)
        for call in self.calls:
            if not only or call.short in only or call.name in only:
                grouped[call.message_id or "one response"].append(call)
        return dict(grouped)

    def by_subagent(self) -> dict[str, list[Call]]:
        """Calls made from inside a subagent, grouped by which one made them."""
        grouped: dict[str, list[Call]] = defaultdict(list)
        for call in self.calls:
            if call.parent_tool_use_id:
                grouped[call.parent_tool_use_id].append(call)
        return dict(grouped)

    def show(self, *, calls=True, reply=True, cost=True, runner=None, limit=500) -> None:
        from .show import show_calls, show_cost, show_reply

        if calls:
            show_calls(self)
        if reply:
            show_reply(self)
        if cost and self.result is not None:
            show_cost(self, runner=runner)


class AgentRunner:
    """Runs an agent under one set of options, and keeps a running total of the spend.

    `strip` is the server prefix to drop from tool names when reporting them, so a run
    over `mcp__support__*` reads as `get_customer` rather than the full wire name.

    `skip` names tools left out of the count. `ToolSearch` is how the SDK loads a
    tool's schema on demand: it is plumbing, not a choice the model made.

    `before` runs ahead of every call, which is how a lab re-arms a fixture so the
    notebook can be run twice.
    """

    def __init__(self, options: ClaudeAgentOptions, *, strip: str = "",
                 skip: Sequence[str] = ("ToolSearch",), before=None):
        self.options = options
        self.strip = strip
        self.skip = tuple(skip)
        self.before = before
        self.spend: list[float] = []

    @property
    def total(self) -> float:
        return sum(self.spend)

    def _options(self, overrides: dict) -> ClaudeAgentOptions:
        return dataclasses.replace(self.options, **overrides) if overrides else self.options

    def _collect(self, message, run: Run) -> None:
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    if block.name in self.skip:
                        continue
                    run.calls.append(Call(
                        name=block.name,
                        input=block.input,
                        short=block.name.replace(self.strip, "") if self.strip else block.name,
                        message_id=message.message_id,
                        parent_tool_use_id=message.parent_tool_use_id,
                    ))
                elif getattr(block, "text", None):
                    run.reply = block.text
        elif isinstance(message, ResultMessage):
            run.result = message
            run.turns += message.num_turns or 0
            run.cost += message.total_cost_usd or 0.0
            run.duration_s += (message.duration_ms or 0) / 1000
            run.denials.extend(message.permission_denials or [])
            run.endings.append(message.subtype)
            if message.structured_output is not None:
                run.structured_output = message.structured_output
            if message.result:
                run.reply = message.result
            self.spend.append(message.total_cost_usd or 0.0)

    async def ask(self, prompt: str, **overrides) -> Run:
        """One prompt, one answer."""
        if self.before:
            self.before()
        run = Run()
        try:
            async for message in query(prompt=prompt, options=self._options(overrides)):
                self._collect(message, run)
        except ResultError as exc:
            # max_budget_usd is a real stop rather than a warning: crossing it ends the
            # run with an error instead of a result.
            print(f"the run stopped early: {exc}")
        return run

    async def converse(self, turns: Sequence[str], **overrides) -> Run:
        """A scripted conversation, over one session.

        A support conversation is not one request: what the agent does next depends on
        what the customer said, so the turns share a client and a context.
        """
        if self.before:
            self.before()
        run = Run()
        async with ClaudeSDKClient(options=self._options(overrides)) as client:
            for turn in turns:
                await client.query(turn)
                async for message in client.receive_response():
                    self._collect(message, run)
        return run
