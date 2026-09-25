"""Printing, in the four shapes a lab actually needs.

A notebook cell should end with a result, not with a paragraph. These helpers cover
what the agent said, what it called, what a tool returned, and what it cost; anything
else a cell wants to say belongs in the markdown beside it.

A cell that runs several conversations is the one case printing alone cannot serve: the
replies are the point and they are far too long to sit in the flow of the notebook.
`show_transcript` puts them in a panel with its own scrollbar, so they can be read whole
without pushing the next cell off the screen.
"""

from __future__ import annotations

import html
import json
import textwrap
from itertools import zip_longest
from typing import Any, Iterable, Mapping, Sequence

__all__ = [
    "show_calls", "show_reply", "show_transcript", "show_cost", "show_denials",
    "show_payload", "show_table", "show_tools", "collapse", "brief", "FONT",
]

ARROW = "→"

# Single quotes: this stack is interpolated into a double-quoted style attribute.
FONT = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace"


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


def _turns_of(run) -> list[tuple[str, str]]:
    """One (customer, agent) pair per turn.

    `converse` records both sides as it goes; a run from before that, or one built by
    hand, still has its last reply, so it shows as a single unattributed turn.
    """
    prompts = list(getattr(run, "prompts", None) or [])
    replies = list(getattr(run, "replies", None) or [])
    if not replies and getattr(run, "reply", ""):
        replies = [run.reply]
    return list(zip_longest(prompts, replies, fillvalue=""))


def _sections(runs, label: str) -> list[tuple[str, list[tuple[str, str]]]]:
    """Whatever a cell happens to be holding -> [(heading, turns)].

    A suite of conversations is already a mapping of number to run, so that is the
    shape this takes; a list or a lone run works too.
    """
    if isinstance(runs, Mapping):
        headings = [f"{label} {key}".strip() for key in runs]
        subjects = list(runs.values())
    elif isinstance(runs, (list, tuple)):
        headings = [f"{label} {number}".strip() for number in range(1, len(runs) + 1)]
        subjects = list(runs)
    else:
        headings, subjects = [label], [runs]
    return [(heading, _turns_of(run)) for heading, run in zip(headings, subjects)]


# The labs are read on a dark screen, so the panel is the same dark card the source
# helper renders code on. Colours are written onto the elements rather than into a
# stylesheet, because a notebook's output has no stylesheet of its own to extend.
PANEL = {"background": "#0d1117", "text": "#e6edf3", "quiet": "#8b949e",
         "heading": "#79c0ff", "rule": "#21262d"}


def _panel(sections, height: int, title: str) -> str:
    def block(speaker: str, said: str, colour: str) -> str:
        return (f'<div style="margin:8px 0 0;color:{colour};white-space:pre-wrap">'
                f'<span style="color:{PANEL["quiet"]}">{speaker}: </span>'
                f"{html.escape(said)}</div>")

    parts = []
    if title:
        parts.append(f'<div style="color:{PANEL["quiet"]};margin-bottom:8px">'
                     f"{html.escape(title)}</div>")
    for index, (heading, turns) in enumerate(sections):
        rule = "" if index == 0 else (f'border-top:1px solid {PANEL["rule"]};'
                                      "margin-top:16px;padding-top:12px;")
        if heading or rule:
            parts.append(f'<div style="{rule}color:{PANEL["heading"]};font-weight:600">'
                         f"{html.escape(heading)}</div>")
        for prompt, reply in turns:
            if prompt:
                parts.append(block("customer", prompt, PANEL["quiet"]))
            parts.append(block("agent", reply.strip() or "(no final text)", PANEL["text"]))
    return (
        f'<div style="background:{PANEL["background"]};border-radius:6px;'
        f"padding:12px 14px;max-height:{height}px;overflow-y:auto;"
        f'color:{PANEL["text"]};font-family:{FONT};font-size:0.88em;line-height:1.5">'
        + "".join(parts) + "</div>"
    )


def _plain(sections, title: str) -> str:
    lines = [title] if title else []
    for heading, turns in sections:
        lines += ["", heading] if heading else [""]
        for prompt, reply in turns:
            if prompt:
                lines.append(f"  customer: {prompt}")
            lines.append("  agent:")
            lines += [f"    {line}" for line in
                      (reply.strip() or "(no final text)").splitlines()]
    return "\n".join(lines).strip("\n")


def show_transcript(runs, *, label: str = "", title: str = "", height: int = 420) -> None:
    """Every turn of every conversation, in a panel with its own scrollbar.

    Takes the mapping of number to run that a suite of conversations already is, or a
    list, or one run. `label` prefixes the mapping's keys, so `label="conversation"`
    heads the sections `conversation 1`, `conversation 2`.

    Nothing is truncated here. A scrollbar is the alternative to picking a limit and
    hoping the sentence that decides the case falls above it.

    Anywhere the HTML is not rendered, a terminal or nbconvert, the same call falls
    back to the plain text in the second half of the bundle.
    """
    from IPython.display import display

    sections = _sections(runs, label)
    display({"text/html": _panel(sections, height, title),
             "text/plain": _plain(sections, title)}, raw=True)


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
