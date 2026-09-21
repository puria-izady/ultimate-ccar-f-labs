"""labkit: the plumbing the lab notebooks do not need to show you.

The labs are about MCP servers, tool definitions, agent definitions, hooks and the
options you run an agent under. Everything else is here: finding the workspace, reading the
credential, driving a run, printing a result. So a notebook cell holds the primitive and the
proof and very little else.

Nothing here is a lesson. Read it if you are curious; you never have to.

`labkit.extract` is deliberately not re-exported: lab 5 calls the Claude API directly
rather than through the Agent SDK, and keeping the two namespaces apart is the point.
"""

from .hooks import decision, fire, updated_output
from .lab import Lab, start
from .runner import NO_CONNECTORS, AgentRunner, Call, Run, options
from .sdktools import call as call_sdk_tool
from .show import (
    brief, collapse, show_calls, show_cost, show_denials, show_payload, show_reply,
    show_table, show_tools,
)
from .source import ToolSpec, show_source, source, tool_specs

__version__ = "0.3.0"

__all__ = [
    "Lab", "start",
    "AgentRunner", "Run", "Call", "options", "NO_CONNECTORS",
    "call_sdk_tool",
    "fire", "decision", "updated_output",
    "source", "show_source", "tool_specs", "ToolSpec",
    "show_calls", "show_reply", "show_cost", "show_denials", "show_payload",
    "show_table", "show_tools", "collapse", "brief",
]
