"""Lab 3's gates, exercised the way the SDK calls them.

These are the lab's central claim — that a rule written as code holds on every run —
so they get real tests rather than only a notebook cell.
"""

import asyncio
import json
import sys
from pathlib import Path

import pytest

import labkit

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lab_03"))

import fixtures                      # noqa: E402
import support.hooks as H            # noqa: E402
import support.tools as T            # noqa: E402


def run(coroutine):
    """These are all plain coroutines, so no async test plugin is needed to drive them."""
    return asyncio.run(coroutine)


REFUND = {"order_id": "ORD-0003", "customer_id": "CUST-0001", "amount": 89.99,
          "reason": "damaged on arrival"}


@pytest.fixture(autouse=True)
def workspace(tmp_path, monkeypatch):
    """Build the fixture somewhere disposable and point the tools at it."""
    monkeypatch.setattr(T, "DATA", fixtures.build(tmp_path))
    T.reset()
    H.reset()


def verified_response(identifier):
    """The content blocks a hook would really be handed."""
    return run(T.get_customer.handler({"identifier": identifier}))["content"]


def test_the_gate_is_shut_before_any_verification():
    verdict = labkit.decision(
        run(labkit.fire(H.require_verification, "mcp__support__process_refund",
                        tool_input=REFUND)))
    assert verdict is not None and verdict[0] == "deny"
    assert "get_customer" in verdict[1], "a denial has to name the way forward"


def test_two_candidates_record_nothing_so_the_gate_stays_shut():
    run(labkit.fire(H.record_verification, "mcp__support__get_customer",
                    tool_response=verified_response("Sam Okafor")))
    assert H.case["verified_customer_id"] is None
    assert labkit.decision(
        run(labkit.fire(H.require_verification, "mcp__support__lookup_order"))) is not None


def test_exactly_one_match_opens_the_gate():
    run(labkit.fire(H.record_verification, "mcp__support__get_customer",
                    tool_response=verified_response("ivan.petrov@example.com")))
    assert H.case["verified_customer_id"] == "CUST-0001"
    assert labkit.decision(
        run(labkit.fire(H.require_verification, "mcp__support__process_refund",
                        tool_input=REFUND))) is None


@pytest.mark.parametrize("amount,blocked", [(89.99, False), (500.00, False), (650.00, True)])
def test_the_refund_limit_blocks_above_it_and_not_at_it(amount, blocked):
    verdict = labkit.decision(
        run(labkit.fire(H.enforce_refund_limit, "mcp__support__process_refund",
                        tool_input={**REFUND, "amount": amount})))
    assert (verdict is not None) is blocked
    if blocked:
        assert "escalate_to_human" in verdict[1], "a refusal must redirect, not dead-end"


@pytest.mark.parametrize("shape", ["list", "wrapped"])
def test_the_normaliser_reads_both_response_shapes_and_puts_them_back(shape):
    raw = run(T.lookup_order.handler({"order_id": "ORD-0003", "customer_id": "CUST-0001"}))
    response = raw["content"] if shape == "list" else raw
    updated = labkit.updated_output(
        run(labkit.fire(H.normalise_tool_output, "mcp__support__lookup_order",
                        tool_response=response)))
    blocks = updated if shape == "list" else updated["content"]
    after = json.loads(blocks[0]["text"])
    assert after["status"] == "delivered", "the numeric status code is labelled"
    assert set(after) == set(H.KEEP) | {"fields_dropped"}
    assert after["fields_dropped"] == 33 - len(H.KEEP)


def test_unix_timestamps_become_iso_8601():
    raw = run(T.get_customer.handler({"identifier": "CUST-0001"}))
    updated = labkit.updated_output(
        run(labkit.fire(H.normalise_tool_output, "mcp__support__get_customer",
                        tool_response=raw["content"])))
    after = json.loads(updated[0]["text"])
    assert after["created"].startswith("20") and "T" in after["created"]


def test_the_transient_timeout_fires_once_and_reset_re_arms_it():
    args = {"order_id": "ORD-0009", "customer_id": "CUST-0007"}
    first, _ = run(labkit.call_sdk_tool(T.lookup_order, **args))
    second, _ = run(labkit.call_sdk_tool(T.lookup_order, **args))
    assert (first, second) == (True, False), "a retry is worth making exactly once"
    T.reset()
    again, _ = run(labkit.call_sdk_tool(T.lookup_order, **args))
    assert again is True, "reset() puts the failure back so the notebook can be rerun"


def test_a_handoff_pointing_at_the_transcript_is_refused():
    is_error, payload = run(labkit.call_sdk_tool(
        T.escalate_to_human,
        customer_id="CUST-0001",
        root_cause="The customer is unhappy, as discussed above, and wants a refund.",
        refund_amount="650.00",
        recommended_action="Please take a look and sort it out for them."))
    assert is_error, "all four fields are present and it is still not self-contained"
