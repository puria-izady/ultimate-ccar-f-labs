"""Printing, in the four shapes a lab actually needs.

A notebook cell should end with a result, not with a paragraph. These helpers cover
what the agent said, what it called, what a tool returned, and what it cost; anything
else a cell wants to say belongs in the markdown beside it.
"""

from __future__ import annotations

import json
import textwrap
from typing import Any, Iterable, Mapping, Sequence

__all__ = [
    "show_calls", "show_reply", "show_cost", "show_denials", "show_payload",
    "show_table", "show_tools", "collapse", "brief",
]

ARROW = "→"


def brief(value: Any, width: int = 72) -> str:
    """One line of JSON, cut to width."""
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    return text if len(text) <= width else text[: width - 1] + "…"


def collapse(names: Iterable[str]) -> list[str]:
    """['Grep', 'Grep', 'Read'] -> ['Grep x2', 'Read'].

    Consecutive repeats are the interesting signal when a tool is being retried, and
    they are noise when they are not. Collapsing is a display choice, never a data one:
    anything that counts calls must count the uncollapsed list.
    """
    runs: list[list] = []
    for name in names:
        if runs and runs[-1][0] == name:
            runs[-1][1] += 1
        else:
            runs.append([name, 1])
    return [name if count == 1 else f"{name} x{count}" for name, count in runs]


def _calls_of(subject):
    return getattr(subject, "calls", subject)


def show_calls(subject, *, collapse_repeats: bool = False, width: int = 72,
               label: str = "tool calls") -> None:
    """Every tool the agent reached for, in order, with its arguments."""
    calls = list(_calls_of(subject))
    if not calls:
        print(f"{label}: none")
        return
    names = [getattr(call, "short", None) or getattr(call, "name", call[0]) for call in calls]
    print(f"{label}: {' '.join(collapse(names)) if collapse_repeats else ', '.join(names)}")
    if collapse_repeats:
        return
    for call, name in zip(calls, names):
        arguments = getattr(call, "input", None)
        if arguments is None and isinstance(call, tuple):
            arguments = call[1]
        print(f"  {ARROW} {name}({brief(arguments or {}, width)})")


def show_reply(subject, *, limit: int = 500, label: str = "agent") -> None:
    """What the agent said last, indented so it reads as a quotation."""
    text = (getattr(subject, "reply", subject) or "").strip() or "(no final text)"
    print(f"{label}:")
    for line in text[:limit].splitlines():
        print(f"  {line}")
    if len(text) > limit:
        print("  …")


def show_cost(run, *, runner=None) -> None:
    """The one line worth keeping about spend."""
    parts = [f"${run.cost:.4f}", f"{run.turns} turns"]
    if getattr(run, "duration_s", None):
        parts.append(f"{run.duration_s:.1f}s")
    total = f"   (notebook total ${runner.total:.4f})" if runner is not None else ""
    print("  ".join(parts) + total)


def show_denials(run) -> None:
    """What the hooks stopped. An empty list is itself a result worth printing."""
    denials = list(getattr(run, "denials", []) or [])
    if not denials:
        print("permission denials: none")
        return
    print(f"permission denials: {len(denials)}")
    for denial in denials:
        name = str(denial.get("tool_name", "?")).split("__")[-1]
        print(f"  DENIED {name}({brief(denial.get('tool_input') or {}, 58)})")


def show_payload(payload: Mapping, *, label: str = "", keys: Sequence[str] | None = None,
                 is_error: bool | None = None) -> None:
    """What a tool returned, one field per line.

    `keys` picks the fields that matter; without it every field is shown. The error
    flag is printed when it is given, because whether a result is a failure is a
    separate question from what the payload says.
    """
    if label or is_error is not None:
        flag = "" if is_error is None else ("REFUSED  " if is_error else "ok       ")
        print(f"{flag}{label}".rstrip())
    indent = "  " if (label or is_error is not None) else ""
    for key in keys or payload:
        if key in payload and payload[key] not in (None, "", [], {}):
            print(f"{indent}{key:<24} {brief(payload[key], 84)}")


def show_table(rows: Iterable[Sequence], *, headers: Sequence[str] = (),
               wrap: Mapping[str, int] | None = None) -> None:
    """A plain aligned table, so no notebook has to hand-count column widths again.

    `wrap` maps a header to a width and folds that column over several lines, which is
    how a tool description stays readable next to its name.
    """
    rows = [[("" if cell is None else str(cell)) for cell in row] for row in rows]
    if not rows:
        return
    columns = len(rows[0])
    limits = {}
    if wrap and headers:
        limits = {headers.index(name): width for name, width in wrap.items() if name in headers}

    widths = [
        max(
            [len(headers[index]) if index < len(headers) else 0]
            + [min(len(row[index]), limits.get(index, 10**6)) for row in rows]
        )
        for index in range(columns)
    ]
    if headers:
        print("  ".join(str(head).ljust(widths[index]) for index, head in enumerate(headers)))
        print("  ".join("-" * width for width in widths))

    for row in rows:
        folded = [
            textwrap.wrap(cell, limits[index]) or [""] if index in limits else [cell]
            for index, cell in enumerate(row)
        ]
        for line in range(max(len(part) for part in folded)):
            cells = [
                (folded[index][line] if line < len(folded[index]) else "").ljust(widths[index])
                for index in range(columns)
            ]
            print("  ".join(cells).rstrip())


def show_tools(tools) -> None:
    """Name, description and argument descriptions: the whole basis on which Claude chooses.

    Takes MCP tool objects, Agent SDK tool objects, or the ToolSpec records that
    labkit.source.tool_specs reads straight out of a file.
    """
    for tool in tools:
        print(tool.name)
        print(f"    {tool.description}")
        schema = getattr(tool, "inputSchema", None) or getattr(tool, "input_schema", None)
        properties = schema.get("properties", schema) if isinstance(schema, dict) else {}
        for argument, spec in (properties or {}).items():
            note = spec.get("description", "(none)") if isinstance(spec, dict) else spec
            print(f"    {argument}: {note}")
        print()
