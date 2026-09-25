"""Four tools over the research corpus, two channels apart.

`load_document` is the constrained replacement for a generic fetcher. A generic fetcher
takes any URL at all, including one an agent invented, and returns something plausible
for it, which is how a source nobody can check ends up cited in a report. This one
refuses anything outside the corpus and says what to do instead.

A refusal carries six fields, defined once in `failed` and nowhere else. Each answers
exactly one question the caller has to answer anyway:

| Field | The question it answers |
|---|---|
| `status` | did it fail |
| `failure_type` | is a retry worth trying |
| `attempted_query` | what should a retry change |
| `partial_results` | what is already usable |
| `alternative_approaches` | which other route could work |
| `coverage_impact` | what gap must the report annotate |

`is_error` is what marks a failure on the wire. A tool that returns an error dictionary
without it is reported as a success, which is how a failure quietly becomes "nothing
found".
"""

from __future__ import annotations

import json
import re
from typing import Annotated

from claude_agent_sdk import tool

from corpus import BY_URL, DOCS, FIELD_WORDS

__all__ = ["TOOLS", "search_web", "search_internal", "load_document", "verify_fact",
           "ok", "failed"]


def ok(payload):
    return {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}]}


def failed(kind, *, attempted, impact, alternatives, partial=None):
    """The six-field contract, defined here and nowhere else."""
    payload = {"status": "partial_failure", "failure_type": kind,
               "attempted_query": attempted, "partial_results": partial or [],
               "alternative_approaches": alternatives, "coverage_impact": impact}
    return {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
            "is_error": True}


def results(query, channel):
    asked = set(re.findall(r"[a-z]+", query.lower()))
    hits = [{key: doc[key] for key in ("title", "url", "publisher", "publication_date",
                                       "collection_period", "excerpt")}
            for doc in DOCS
            if doc["channel"] == channel and asked & FIELD_WORDS[doc["field"]]]
    return ok({"status": "success", "channel": channel, "attempted_query": query,
               "results": hits,
               "note": "" if hits else "The search ran and matched nothing on this channel."})


@tool(
    "search_web",
    "Search the published channel: trade research, sector monitors and official statistics "
    "about AI in the creative industries. Use it to survey what has been reported publicly "
    "about a field. Do not use it for one organisation own records (use search_internal). "
    "Every hit carries a title, a URL, a publisher, a publication date, the period measured "
    "and a verbatim excerpt. A search that matches nothing returns an empty list, which is "
    "an answer and not an error.",
    {"query": Annotated[str, "What to search for, in plain words."]},
)
async def search_web(args):
    return results(str(args.get("query", "")), "web")


@tool(
    "search_internal",
    "Search the internal channel: one organisation own reviews, notes and ledger extracts. "
    "Use it to find what was recorded inside the organisation about a field. Do not use it "
    "for published sector research (use search_web). Hits carry the same provenance as the "
    "published channel. A search that matches nothing returns an empty list, which is an "
    "answer and not an error.",
    {"query": Annotated[str, "What to search for, in plain words."]},
)
async def search_internal(args):
    return results(str(args.get("query", "")), "internal")


@tool(
    "load_document",
    "Open one document from the research corpus by URL and return its full text and "
    "provenance. The URL must be one a search returned. Use it to read a source before "
    "quoting from it. Do not use it to search. A URL outside the corpus is refused, with "
    "what to do instead.",
    {"url": Annotated[str, "A URL returned by search_web or search_internal."]},
)
async def load_document(args):
    url = str(args.get("url", "")).strip()
    doc = BY_URL.get(url)
    if doc is None:
        return failed(
            "validation", attempted=url,
            impact="This source contributes nothing until it is replaced.",
            alternatives=["Open a URL that search_web or search_internal actually returned"],
            # what is already usable and need not be redone: the documents that do open
            partial=[{"title": d["title"], "url": d["url"]} for d in DOCS],
        )
    return ok({"status": "success", **{k: v for k, v in doc.items() if k != "excerpt"}})


@tool(
    "verify_fact",
    "Check one claim against one corpus document: does the excerpt you were given really "
    "appear in that source, and what are its date and period? Use it while writing up, to "
    "confirm a finding before it goes into the report. Do not use it to find sources.",
    {"claim": Annotated[str, "The claim as it would appear in the report."],
     "url": Annotated[str, "The corpus URL the claim is attributed to."],
     "excerpt": Annotated[str, "The wording said to appear in that source."]},
)
async def verify_fact(args):
    url = str(args.get("url", "")).strip()
    doc = BY_URL.get(url)
    if doc is None:
        return failed("validation", attempted=url, impact="This claim stays unverified.",
                      alternatives=["Verify against a URL a search returned"])
    excerpt = " ".join(str(args.get("excerpt", "")).split()).lower()
    found = bool(excerpt) and excerpt in " ".join(doc["text"].split()).lower()
    return ok({"status": "success", "verified": found, "url": url,
               "claim": str(args.get("claim", "")),
               "publication_date": doc["publication_date"],
               "collection_period": doc["collection_period"],
               "note": "" if found else "That wording does not appear in this source."})


TOOLS = [search_web, search_internal, load_document, verify_fact]
