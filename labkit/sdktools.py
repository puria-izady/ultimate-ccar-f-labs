"""Calling an Agent SDK tool directly.

`@tool` returns an `SdkMcpTool` object rather than a function, so the body is reached
through `.handler`, and the answer travels as JSON inside a typed content block.

There is deliberately no helper here for lab 1's FastMCP tools. Those stay ordinary
callables, and a failure there has to be **raised** rather than returned, which is
exactly the contrast lab 1 and lab 3 are built to show. One helper covering both would
erase it.
"""

from __future__ import annotations

import json

__all__ = ["call"]


async def call(tool, **arguments) -> tuple[bool, dict]:
    """Run one SDK tool. Returns (is_error, payload).

    The flag comes first because whether the call failed is a separate question from
    what the payload says, and it is the one an agent has to answer first.
    """
    result = await tool.handler(arguments)
    payload = json.loads(result["content"][0]["text"])
    return bool(result.get("is_error")), payload
