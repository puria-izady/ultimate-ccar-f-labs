"""The policy around the tools: what may run, and what the model gets to read.

Two jobs, and they happen at different moments. `PostToolUse` sees a result before the
model does and can replace it, which is transformation. `PreToolUse` runs before the
call goes out and can refuse it, which is prevention. A hook cannot un-run a call, so
anything that must not happen belongs in the second kind.

None of this asks the model for anything, so none of it has a failure rate.
"""

import json
from datetime import datetime, timezone

REFUND_LIMIT = 500.0
GATED = ("mcp__support__lookup_order", "mcp__support__process_refund")
STATUS_NAMES = {10: "placed", 20: "dispatched", 30: "delivered", 40: "returned",
                50: "cancelled"}
KEEP = ("order_id", "status", "delivered_at", "total_pence", "item_name")
NEWLINE = chr(10)

# What the harness remembers between calls. The verified id is what the gate checks;
# the issues are the case facts, kept verbatim and never summarised.
case = {"verified_customer_id": None, "customer_name": None, "issues": []}


def reset():
    case.update(verified_customer_id=None, customer_name=None, issues=[])


def payload_of(response):
    """An MCP tool answers with typed content blocks, so the JSON a rule needs is
    inside a text block rather than at the top of the response. Measured against the
    SDK, a hook is handed the block list itself. Read that, the wrapped form, and a
    plain dictionary, and remember which one came in."""
    blocks = None
    shape = None
    if isinstance(response, list):
        blocks, shape = response, "list"
    elif isinstance(response, dict) and isinstance(response.get("content"), list):
        blocks, shape = response["content"], "wrapped"
    if blocks is not None:
        for block in blocks:
            if isinstance(block, dict) and block.get("type") == "text":
                try:
                    return json.loads(block["text"]), shape
                except (ValueError, KeyError, TypeError):
                    return None, None
        return None, None
    if isinstance(response, dict):
        return response, "dict"
    return None, None


def repack(response, payload, shape):
    block = {"type": "text", "text": json.dumps(payload, indent=2)}
    if shape == "list":
        return [block]
    if shape == "wrapped":
        out = dict(response)
        out["content"] = [block]
        return out
    return payload


async def normalise_tool_output(input_data, tool_use_id, context):
    """PostToolUse. Unix to ISO 8601, status code to label, thirty-three fields to five."""
    payload, shape = payload_of(input_data.get("tool_response"))
    if payload is None:
        return {}
    normalised = dict(payload)
    changed = False
    for field in ("created", "last_contact_at"):
        value = normalised.get(field)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            normalised[field] = datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
            changed = True
    status = normalised.get("status")
    if isinstance(status, int) and not isinstance(status, bool):
        normalised["status"] = STATUS_NAMES.get(status, str(status))
        changed = True
    if input_data.get("tool_name") == "mcp__support__lookup_order" and "total_pence" in normalised:
        trimmed = {key: normalised[key] for key in KEEP if key in normalised}
        trimmed["fields_dropped"] = len(normalised) - len(trimmed)
        normalised, changed = trimmed, True
    if not changed:
        return {}
    return {"hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "updatedToolOutput": repack(input_data["tool_response"], normalised, shape),
    }}


async def record_verification(input_data, tool_use_id, context):
    """PostToolUse. Remember the verified id, and only on exactly one match.

    Two candidates record nothing, so the gate below stays shut and the agent has to
    ask for another identifier. The ambiguity rule and the ordering rule turn out to be
    the same mechanism.
    """
    if input_data.get("tool_name") != "mcp__support__get_customer":
        return {}
    payload, _ = payload_of(input_data.get("tool_response"))
    if payload and payload.get("matches") == 1 and payload.get("verified_customer_id"):
        case["verified_customer_id"] = payload["verified_customer_id"]
        case["customer_name"] = payload.get("name")
    return {}


async def require_verification(input_data, tool_use_id, context):
    """PreToolUse. Deny the downstream tools until the prerequisite has returned.

    The reason comes back to the agent as the tool result, so it reads why it was
    stopped and calls get_customer next. A denial that teaches self-corrects; a bare
    refusal makes the agent guess.
    """
    if input_data.get("tool_name") in GATED and not case["verified_customer_id"]:
        return {"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Verify the customer with get_customer before any order or refund "
                "operation. If more than one account matched, ask the customer for "
                "another identifier first, then verify."),
        }}
    return {}


async def enforce_refund_limit(input_data, tool_use_id, context):
    """PreToolUse. Block, and redirect by naming the workflow that can proceed."""
    if input_data.get("tool_name") != "mcp__support__process_refund":
        return {}
    try:
        amount = float(input_data.get("tool_input", {}).get("amount") or 0)
    except (TypeError, ValueError):
        amount = 0.0
    if amount > REFUND_LIMIT:
        return {"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "A refund of " + format(amount, ".2f") + " pounds is over the "
                + format(REFUND_LIMIT, ".0f") + " pound agent limit and needs a human. "
                "Call escalate_to_human with the customer id, the root cause, the "
                "amount and a recommended action."),
        }}
    return {}


def note_issue(kind, reference, amount, status):
    """One record per concern, so an amount never attaches to the wrong order."""
    for issue in case["issues"]:
        if issue["reference"] == reference:
            issue.update(amount=amount, status=status)
            return
    case["issues"].append({"kind": kind, "reference": reference, "amount": amount,
                           "status": status})


def render_facts():
    """The case facts block. Identifiers, amounts and statuses verbatim: a summary
    would blur 40.00 into "about forty pounds" and the wrong order would be refunded."""
    verified = case["verified_customer_id"] or "not yet verified"
    state = "verified" if case["verified_customer_id"] else "unverified"
    lines = ["=== CASE FACTS ===", "CUSTOMER  " + verified + "  " + state]
    for number, issue in enumerate(case["issues"], 1):
        lines.append("ISSUE " + str(number) + "   " + issue["kind"])
        lines.append(("  " + issue["reference"] + "   " + issue["amount"]).rstrip())
        lines.append("  status  " + issue["status"])
    lines.append("===")
    return NEWLINE.join(lines)
