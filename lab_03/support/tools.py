"""Four support tools, served in-process by the Agent SDK.

Half of a tool's job is answering. The other half is failing in a shape the agent can
act on, which is what `failure` is for: a category, whether a retry can help, and what
to do instead.

`is_error` is what marks a failure on the wire. A tool that returns an error-shaped
dictionary without it is reported as a success. Lab 1's FastMCP tools had to **raise**
for the same reason; an SDK tool returns the flag instead.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from claude_agent_sdk import create_sdk_mcp_server, tool
from pydantic import BaseModel, Field, ValidationError, field_validator

DATA = Path(__file__).resolve().parent.parent / "workspace" / "data"
REFUND_WINDOW_DAYS = 30

FLAKY = {"ORD-0009"}          # the orders API times out on this one, once
_timed_out = set()


def reset():
    """Put the transient failure back, so the notebook can be rerun."""
    _timed_out.clear()


def load(name):
    return json.loads((DATA / (name + ".json")).read_text(encoding="utf-8"))


def ok(payload):
    return {"content": [{"type": "text", "text": json.dumps(payload, indent=2)}]}


def failure(category, message, retryable, **extra):
    """A failure the agent can act on, rather than one it has to guess about."""
    payload = {"errorCategory": category, "isRetryable": retryable, "message": message}
    payload.update(extra)
    return {"content": [{"type": "text", "text": json.dumps(payload, indent=2)}],
            "is_error": True}


def mask(value, keep=2):
    head, _, tail = value.partition("@")
    hidden = head[:keep] + "*" * max(len(head) - keep, 1)
    return hidden + ("@" + tail if tail else "")


@tool(
    "get_customer",
    "Verify who you are talking to, from an email address, a phone number or a customer "
    "id. Returns a verified customer id only when exactly one account matches. When more "
    "than one matches it returns every candidate and no verified id, so ask the customer "
    "for another identifier rather than choosing one. Call this before any order or "
    "refund tool.",
    {"identifier": str},
)
async def get_customer(args):
    raw = str(args["identifier"]).strip()
    needle = raw.lower()
    matches = [c for c in load("customers")
               if needle in (c["customer_id"].lower(), c["email"].lower(),
                             c["phone"].lower(), c["name"].lower())]
    if not matches:
        return failure(
            "validation", "No account matches " + raw + ".", True,
            suggestion="Ask for the email address, phone number or an order number.")
    if len(matches) > 1:
        # A successful query with an ambiguous answer. Returning one "most likely"
        # match here would hide the ambiguity instead of resolving it.
        return ok({
            "matches": len(matches),
            "verified_customer_id": None,
            "candidates": [{"customer_id": c["customer_id"], "name": c["name"],
                            "email_hint": mask(c["email"]),
                            "phone_hint": "*******" + c["phone"][-3:]} for c in matches],
            "next_action": "Ask the customer for an email address, phone number or order "
                           "number before taking any customer-specific action.",
        })
    found = dict(matches[0])
    found["matches"] = 1
    found["verified_customer_id"] = found["customer_id"]
    return ok(found)


@tool(
    "lookup_order",
    "Fetch the full order record for one order id: status, dates, amounts, item and "
    "shipment. Requires a customer id already verified by get_customer. Use it to "
    "establish what was ordered and when it arrived before deciding anything.",
    {"order_id": str, "customer_id": str},
)
async def lookup_order(args):
    order_id = str(args["order_id"]).strip().upper()
    if order_id in FLAKY and order_id not in _timed_out:
        _timed_out.add(order_id)
        return failure("transient", "Timed out after 5000 ms calling the orders API.",
                       True, attempted_query="order_id=" + order_id, partial_results=None)
    for record in load("orders"):
        if record["order_id"] == order_id:
            return ok(record)
    return failure("validation", "No order " + order_id + " on this account.", True,
                   suggestion="Ask the customer to read the order number from their email.")


@tool(
    "process_refund",
    "Refund an amount in pounds against a delivered order, giving a reason. Requires a "
    "verified customer id. Refuses anything outside the refund window. The agent refund "
    "limit is enforced outside this tool, as policy, not as code you can edit here.",
    {"order_id": str, "customer_id": str, "amount": float, "reason": str},
)
async def process_refund(args):
    order_id = str(args["order_id"]).strip().upper()
    record = next((r for r in load("orders") if r["order_id"] == order_id), None)
    if record is None:
        return failure("validation", "No order " + order_id + " on this account.", True,
                       suggestion="Confirm the order number with the customer.")
    delivered = datetime.fromisoformat(record["delivered_at"])
    age = (datetime.now(timezone.utc) - delivered).days
    if age > REFUND_WINDOW_DAYS:
        # A business refusal: never retryable, and it carries language the agent can
        # say out loud to the customer rather than a code it has to translate.
        return failure(
            "business",
            "This order was delivered " + str(age) + " days ago, which is outside the "
            + str(REFUND_WINDOW_DAYS) + " day refund window, so a refund cannot be "
            "processed. A replacement or store credit is available instead, and a human "
            "can approve an exception if the customer needs one.",
            False, policy="refund_window", delivered_days_ago=age,
            window_days=REFUND_WINDOW_DAYS, alternatives=["replacement", "store_credit"])
    return ok({"refund_id": "REF-" + order_id[-4:], "order_id": order_id,
               "amount": round(float(args["amount"]), 2), "state": "processed",
               "reason": args["reason"]})


TRANSCRIPT_REFERENCES = ("as discussed", "as mentioned", "as noted", "see above",
                         "per our conversation", "the above", "earlier in this chat")


class Handoff(BaseModel):
    """What a human who cannot read the transcript needs in order to act."""

    customer_id: str = Field(min_length=3)
    root_cause: str = Field(min_length=10)
    refund_amount: str = Field(min_length=1)
    recommended_action: str = Field(min_length=10)
    issue_summary: str = ""
    order_id: str = ""
    actions_taken: list[str] = Field(default_factory=list)
    escalation_reason: str = ""

    @field_validator("root_cause", "recommended_action", "issue_summary")
    @classmethod
    def no_transcript_references(cls, value):
        lowered = value.lower()
        for phrase in TRANSCRIPT_REFERENCES:
            if phrase in lowered:
                raise ValueError(
                    "the receiving human cannot read the conversation, so "
                    + repr(phrase) + " points at nothing. State the fact itself.")
        return value


HANDOFF_SCHEMA = {
    "type": "object",
    "properties": {
        "customer_id": {"type": "string", "description": "The verified customer id."},
        "root_cause": {"type": "string",
                       "description": "Why this happened, in one or two sentences."},
        "refund_amount": {"type": "string",
                          "description": "The amount at stake, to the penny, or none."},
        "recommended_action": {"type": "string",
                               "description": "What you think the human should do."},
        "issue_summary": {"type": "string", "description": "What the customer asked for."},
        "order_id": {"type": "string", "description": "The order, when there is one."},
        "actions_taken": {"type": "array", "items": {"type": "string"},
                          "description": "What you already tried, in order."},
        "escalation_reason": {"type": "string",
                              "description": "Which escalation trigger fired."},
    },
    "required": ["customer_id", "root_cause", "refund_amount", "recommended_action"],
}


@tool(
    "escalate_to_human",
    "Hand the case to a human agent. The human cannot see this conversation, so the "
    "summary has to stand on its own: who the customer is, what actually went wrong, "
    "the amount at stake, and what you recommend. Call this when the customer asks for "
    "a person, when policy does not cover the request, or when you cannot make progress.",
    HANDOFF_SCHEMA,
)
async def escalate_to_human(args):
    try:
        handoff = Handoff(**args)
    except ValidationError as exc:
        missing = [".".join(str(p) for p in err["loc"]) for err in exc.errors()]
        return failure(
            "validation",
            "The handoff is not self-contained: " + "; ".join(missing) + ".", True,
            suggestion="Resend with a verified customer id, a root cause, the refund "
                       "amount and a recommended action, each stated in full.")
    return ok({"ticket": "ESC-" + handoff.customer_id[-4:], "state": "queued",
               "handoff": handoff.model_dump()})


TOOLS = [get_customer, lookup_order, process_refund, escalate_to_human]
server = create_sdk_mcp_server(name="support", version="1.0.0", tools=TOOLS)
