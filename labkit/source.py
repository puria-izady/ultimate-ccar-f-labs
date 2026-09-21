"""Show the code that is the lesson, and only that code.

The lab notebooks keep their tool, hook and server definitions in real Python files
beside the notebook, so they are syntax highlighted, lintable and openable in an
editor. These helpers lift one definition out of such a file and render it where the
notebook needs it.

Slicing is done on the AST rather than with `inspect.getsource`, for two reasons that
both matter here. An Agent SDK `@tool` object is a dataclass, not a function, so
`inspect.getsource` fails on it outright; and reaching past it to `.handler` loses the
decorator, which carries the description, which is half of what labs 1 and 2 teach.
"""

from __future__ import annotations

import ast
import inspect
from dataclasses import dataclass
from pathlib import Path

__all__ = ["source", "show_source", "tool_specs", "ToolSpec"]


def _resolve(target) -> tuple[Path, str]:
    """A path, a module, a function, or an SDK tool object -> the file it lives in."""
    if isinstance(target, (str, Path)):
        path = Path(target)
        if not path.exists():
            raise FileNotFoundError(f"no such file: {path}")
        return path, path.read_text(encoding="utf-8")
    handler = getattr(target, "handler", None)      # an SdkMcpTool keeps the body here
    if handler is not None:
        target = handler
    file = inspect.getsourcefile(target) or inspect.getfile(target)
    path = Path(file)
    return path, path.read_text(encoding="utf-8")


def _span(node) -> tuple[int, int]:
    """First and last line of a definition, counting its decorators."""
    start = node.lineno
    for decorator in getattr(node, "decorator_list", []):
        start = min(start, decorator.lineno)
    return start, node.end_lineno


def _named(node) -> str | None:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return node.name
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        return target.id if isinstance(target, ast.Name) else None
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id
    return None


def _lead_comment(lines: list[str], start: int) -> int:
    """Walk back over the comment block sitting directly on top of a definition.

    A comment explaining why a definition looks the way it does belongs with it. A
    blank line ends the block, so an unrelated comment further up is not swallowed.
    """
    index = start - 1                                    # 0-based, the line above
    while index > 0 and lines[index - 1].lstrip().startswith("#"):
        index -= 1
    return index + 1


def source(target, *names: str, comments: bool = True) -> str:
    """The source of `target`, or just the top-level definitions `names` picks out.

    Names may be functions, classes or module constants, and are returned in the order
    they appear in the file rather than the order you asked for them.
    """
    path, text = _resolve(target)
    if not names:
        return text.rstrip("\n")

    lines = text.splitlines()
    tree = ast.parse(text)
    wanted, spans = set(names), []
    for node in tree.body:
        name = _named(node)
        if name in wanted:
            start, end = _span(node)
            if comments:
                start = _lead_comment(lines, start)
            spans.append((start, end, name))

    missing = wanted - {name for _, _, name in spans}
    if missing:
        raise KeyError(f"{path.name} has no top-level {', '.join(sorted(missing))}")

    spans.sort()
    chunks, previous_end = [], None
    for start, end, _ in spans:
        if previous_end is not None and start > previous_end + 1:
            chunks.append("")                            # a blank line stands in for a gap
        chunks.extend(lines[start - 1:end])
        previous_end = end
    return "\n".join(chunks).rstrip("\n")


def show_source(target, *names: str, comments: bool = True) -> None:
    """Render a definition as syntax-highlighted Python, inline in the notebook."""
    from IPython.display import Code, display

    display(Code(data=source(target, *names, comments=comments), language="python"))


@dataclass(frozen=True)
class ToolSpec:
    """What the model is shown about one tool: where it came from, and what it claims."""

    server: str
    name: str
    description: str


def _string(node) -> str | None:
    # Implicitly concatenated literals are already one Constant by the time we see them.
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _server_name(tree: ast.Module, fallback: str) -> str:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        called = node.func
        name = getattr(called, "id", None) or getattr(called, "attr", None)
        if name == "FastMCP" and node.args:
            return _string(node.args[0]) or fallback
        if name == "create_sdk_mcp_server":
            for keyword in node.keywords:
                if keyword.arg == "name":
                    return _string(keyword.value) or fallback
    return fallback


def _spec_from(decorator: ast.Call, function_name: str, server: str) -> ToolSpec | None:
    called = decorator.func
    label = getattr(called, "attr", None) or getattr(called, "id", None)
    if label != "tool":
        return None
    for keyword in decorator.keywords:                   # FastMCP: @mcp.tool(description=...)
        if keyword.arg == "description":
            text = _string(keyword.value)
            if text is not None:
                return ToolSpec(server, function_name, text)
    if len(decorator.args) >= 2:                         # Agent SDK: @tool("name", "desc", {...})
        name, text = _string(decorator.args[0]), _string(decorator.args[1])
        if name is not None and text is not None:
            return ToolSpec(server, name, text)
    return None


def tool_specs(*paths) -> list[ToolSpec]:
    """Every tool's name and description, read out of the files without importing them.

    Importing would mean running the module and, for a stdio server, starting a process.
    Nothing here needs either: the name and the description are literals in the source,
    and they are the entire basis on which the model chooses a tool.
    """
    found = []
    for item in paths:
        path = Path(item)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        server = _server_name(tree, path.stem)
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    spec = _spec_from(decorator, node.name, server)
                    if spec is not None:
                        found.append(spec)
                        break
    return found
