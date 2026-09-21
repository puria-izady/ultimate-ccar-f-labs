"""Calling a hook without a model in the loop.

A hook is an ordinary async function, so the cheapest way to prove one works is to
call it. The SDK hands it three arguments — the event data, the tool use id, and a
context — and this builds all three the way the SDK really does, so what the notebook
proves offline is what will happen on a live run.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

__all__ = ["fire", "decision", "updated_output"]


async def fire(hook, tool_name: str, *, tool_input: dict | None = None,
               tool_response: Any = None, tool_use_id: str = "tu_lab", cwd=None):
    """Call a hook exactly the way the SDK does.

    A `tool_response` makes it a PostToolUse event; without one it is a PreToolUse.
    Every key the SDK's hook input requires is supplied, so a hook that reads one of
    the less obvious ones behaves here as it would in a run.
    """
    event = "PostToolUse" if tool_response is not None else "PreToolUse"
    data = {
        "hook_event_name": event,
        "tool_name": tool_name,
        "tool_input": tool_input or {},
        "tool_use_id": tool_use_id,
        "session_id": "labkit",
        "transcript_path": "",
        "cwd": str(cwd or Path.cwd()),
    }
    if tool_response is not None:
        data["tool_response"] = tool_response
    return await hook(data, tool_use_id, {"signal": None})


def decision(result) -> tuple[str, str] | None:
    """The (decision, reason) a PreToolUse hook returned, or None for no opinion.

    A hook returning {} is how it says: nothing to add, carry on.
    """
    specific = (result or {}).get("hookSpecificOutput") or {}
    verdict = specific.get("permissionDecision")
    return (verdict, specific.get("permissionDecisionReason", "")) if verdict else None


def updated_output(result):
    """What a PostToolUse hook replaced the tool's answer with, or None if it did not."""
    return ((result or {}).get("hookSpecificOutput") or {}).get("updatedToolOutput")
