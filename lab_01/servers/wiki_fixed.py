# The knowledge base, renamed and narrowed so it stops claiming tickets.
#
# Disclaim: this is the fix people miss, and here it is the actual cause. A good
# description says what the tool is NOT for. A tool that over-claims steals calls it
# cannot serve.

from pathlib import Path

from mcp.server.fastmcp import FastMCP
from pydantic import Field

DATA = Path(__file__).resolve().parent.parent / "data"
mcp = FastMCP("wiki")


@mcp.tool(description=(
    "Search the team's long form wiki pages, which are prose written by engineers to explain "
    "standing decisions. Use this for background and rationale. Do not use it for support "
    "tickets or customer reports, which live in the ticket queue."
))
def search_wiki_pages(query: str = Field(description="Search text")) -> dict:
    hits = []
    for path in sorted(DATA.glob("adr/*.md")):
        text = path.read_text()
        if query.lower() in text.lower():
            hits.append({"page": path.stem, "text": text[:300]})
    return {"query": query, "matched": len(hits), "results": hits}


if __name__ == "__main__":
    mcp.run(transport="stdio")
