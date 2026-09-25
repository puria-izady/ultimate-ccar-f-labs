"""The Claude API, for the one lab that calls it directly.

Lab 5 does not use the Agent SDK at all. It calls the Messages API, and its whole
subject is a forced tool call whose *input* schema is the record you want back. That
is a different world from `query()` and `ClaudeSDKClient`, with no result message, no
turns, no cost field and no hooks, which is why this module is not re-exported from
`labkit` and lab 5 imports it by its full name.
"""

from __future__ import annotations

__all__ = ["forced_call", "show_record"]


def forced_call(client, model: str, document: str, tool: dict, *,
                instruction: str = "Extract the record.", max_tokens: int = 1000):
    """One forced tool call, and the block it produced.

    `tool_choice` is what makes Claude call the tool rather than answering in prose.
    The block is found by its **type**, not its position: a forced call usually puts it
    first, and usually is not a contract.

    No `tool_result` goes back. `stop_reason` is `tool_use`, which everywhere else in
    this course means send one; here you already have what you wanted, so you stop.
    """
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": f"{instruction}\n\n{document}"}],
        tools=[tool],
        tool_choice={"type": "tool", "name": tool["name"]},
    )
    return next(block for block in response.content if block.type == "tool_use")


def show_record(record, *, label: str = "", width: int = 18) -> None:
    """The extracted record, one field per line, values shown as Python sees them."""
    if label:
        print(label)
    for key, value in dict(record).items():
        print(f"  {key:<{width}} {value!r}")
