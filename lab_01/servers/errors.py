# Structured failures. Raising is what sets isError on the result; returning a dictionary
# that happens to describe a failure is reported as a success.

import json

RETRYABLE = {"transient": True, "validation": True, "business": False, "permission": False}


class ToolError(ValueError):
    # FastMCP turns a raised exception into a result with isError set.
    pass


def tool_error(category: str, message: str, next_action: str, **extra) -> ToolError:
    if category not in RETRYABLE:
        raise KeyError(f"unknown category {category!r}")
    payload = {
        "errorCategory": category,
        "isRetryable": RETRYABLE[category],
        "message": message,
        "nextAction": next_action,
        **extra,
    }
    return ToolError(json.dumps(payload))
