# Developer productivity tools over the Fernhill workspace.
#
# Read the three descriptions below as if you were the one choosing. The first tool is
# called `lookup` and says `Look things up.` Nothing there tells anyone, human or model,
# that this is the support ticket queue. Part B measures exactly what that costs.
#
# And `architecture_decisions` is doing two jobs: listing what exists, and fetching one.
# A tool that does two things is harder to describe than either of them separately.

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from errors import tool_error

DATA = Path(__file__).resolve().parent.parent / "data"
mcp = FastMCP("devtools")


@mcp.tool(description="Look things up.")
def lookup(query: str = Field(description="Search text")) -> dict:
    tickets = json.loads((DATA / "tickets.json").read_text())
    hits = [t for t in tickets
            if query.lower() in (t["title"] + " " + t["body"]).lower()]
    return {"query": query, "matched": len(hits), "results": hits}


@mcp.tool(description="Get service info.")
def service_catalogue(name: str = Field(description="Service name")) -> dict:
    services = json.loads((DATA / "services.json").read_text())
    for service in services:
        if service["name"] == name:
            return service
    known = ", ".join(s["name"] for s in services)
    raise tool_error(
        "validation",
        f"No service called {name!r}. Expected one of: {known}.",
        "Call again with one of the listed names.",
    )


@mcp.tool(description="Look up decisions.")
def architecture_decisions(
    adr_id: str = Field(default="", description="An ADR id, or empty to list them all"),
) -> dict:
    records = sorted(DATA.glob("adr/ADR-*.md"))
    if not adr_id:
        return {"available": [p.stem for p in records]}
    for path in records:
        if path.stem.startswith(adr_id):
            return {"id": path.stem, "text": path.read_text()}
    raise tool_error(
        "validation",
        f"No decision record {adr_id!r}.",
        "Call again with no id to list the ids that exist.",
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
