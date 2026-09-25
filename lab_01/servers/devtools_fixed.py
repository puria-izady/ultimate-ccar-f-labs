# Developer productivity tools, with the three faults of devtools_server.py fixed.
#
# Describe: every tool says what it is for, when to reach for it, when not to, what goes
# in and what comes back.
# Rename: `lookup` becomes `search_tickets`, which claims its territory in one word.
# Split: `architecture_decisions` did two jobs, so it is now two tools.

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from errors import tool_error

DATA = Path(__file__).resolve().parent.parent / "data"
mcp = FastMCP("devtools")


@mcp.tool(description=(
    "Search the Fernhill support ticket queue by free text. Use this for anything a person "
    "reported: problems, incidents, bugs, customer complaints, and whether a ticket is "
    "still open. Do not use it for documentation or source code. Returns matching tickets "
    "with id, status, owning service, title and body, and a count. A query that matches "
    "nothing returns an empty list, not an error."
))
def search_tickets(query: str = Field(description="Free text, such as 'duplicate charges'")) -> dict:
    tickets = json.loads((DATA / "tickets.json").read_text())
    hits = [t for t in tickets if query.lower() in (t["title"] + " " + t["body"]).lower()]
    return {"query": query, "matched": len(hits), "results": hits}


@mcp.tool(description=(
    "Look up one Fernhill service by its exact name, to find who owns it, who is on call, "
    "and which file it starts from. Use this when you need the owner or the entrypoint of a "
    "named service. Do not use it to search for a service by description. "
    "Returns one service record, or a validation error listing the names that exist."
))
def service_catalogue(name: str = Field(description="Exact service name, such as 'refunds'")) -> dict:
    services = json.loads((DATA / "services.json").read_text())
    for service in services:
        if service["name"] == name:
            return service
    known = ", ".join(s["name"] for s in services)
    raise tool_error("validation", f"No service called {name!r}. Expected one of: {known}.",
                     "Call again with one of the listed names.")


@mcp.tool(description=(
    "List the ids of every architecture decision record. Takes no arguments. "
    "Call this first when you do not already know which record you need, then read one."
))
def list_architecture_decisions() -> dict:
    return {"available": [p.stem for p in sorted(DATA.glob("adr/ADR-*.md"))]}


@mcp.tool(description=(
    "Read the full text of one architecture decision record by its id, such as 'ADR-0005'. "
    "Use this for standing engineering decisions and the reasoning behind them. "
    "Call list_architecture_decisions first if you do not know the id."
))
def read_architecture_decision(adr_id: str = Field(description="An id such as 'ADR-0005'")) -> dict:
    for path in sorted(DATA.glob("adr/ADR-*.md")):
        if path.stem.startswith(adr_id):
            return {"id": path.stem, "text": path.read_text()}
    raise tool_error("validation", f"No decision record {adr_id!r}.",
                     "Call list_architecture_decisions to see the ids that exist.")


if __name__ == "__main__":
    mcp.run(transport="stdio")
