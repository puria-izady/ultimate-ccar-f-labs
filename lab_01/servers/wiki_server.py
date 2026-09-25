# The neighbouring team's knowledge base server.
#
# This is not badly written. Its description is confident and specific, and it is exactly
# the kind of thing a neighbouring team ships happily. It is also claiming support tickets
# it does not hold, which is what makes it win a question it cannot answer.

from pathlib import Path

from mcp.server.fastmcp import FastMCP
from pydantic import Field

DATA = Path(__file__).resolve().parent.parent / "data"
mcp = FastMCP("wiki")


@mcp.tool(description=(
    "Search everything the team has written down, including support tickets, customer "
    "reports, incidents, documents and architecture decisions."
))
def search_knowledge_base(query: str = Field(description="Search text")) -> dict:
    hits = []
    for path in sorted(DATA.glob("adr/*.md")):
        text = path.read_text()
        if query.lower() in text.lower():
            hits.append({"page": path.stem, "text": text[:300]})
    return {"query": query, "matched": len(hits), "results": hits}


if __name__ == "__main__":
    mcp.run(transport="stdio")
