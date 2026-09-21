"""Rendering the finished report.

Formatting, not lesson. The shape being rendered is the `ResearchReport` model defined
in the notebook, and this only reads attributes off it.
"""

from __future__ import annotations

__all__ = ["show_report", "show_spawns"]


def show_report(report) -> None:
    """The three sections, with every source and period kept visible."""
    print(f"topic: {report.topic}\n")

    print(f"WELL ESTABLISHED ({len(report.well_established)})")
    for claim in report.well_established:
        print(f"  [{claim.field_id}] {claim.claim}")
        print(f"      \"{claim.excerpt[:92]}\"")
        print(f"      {claim.source_name}, {claim.source_url} {claim.publication_date}")

    print(f"\nCONTESTED ({len(report.contested)})")
    for entry in report.contested:
        print(f"  {entry.claim}")
        for value in entry.values:
            print(f"      {value.value}  ({value.source_name}, {value.collection_period})")
        print(f"      why they might differ: {entry.possible_explanation}")

    print(f"\nCOVERAGE GAPS ({len(report.coverage_gaps)})")
    for gap in report.coverage_gaps:
        print(f"  [{gap.field_id}/{gap.channel or 'any channel'}] {gap.reason}")


def show_spawns(run) -> None:
    """Which searchers were spawned together, and what each one went on to call.

    Several spawn calls in a single response run at the same time, so grouping by the
    response they arrived in is what tells parallel work from sequential work. Counting
    the calls would not: the same four spawns spread over four turns look identical.
    """
    for index, group in enumerate(run.by_response(only=["Agent", "Task"]).values(), 1):
        kinds = [call.input.get("subagent_type", "?") for call in group]
        together = "together" if len(kinds) > 1 else "on its own"
        print(f"  response {index}: {', '.join(kinds)}  ({together})")

    for index, calls in enumerate(run.by_subagent().values(), 1):
        print(f"  subagent {index} used: {', '.join(call.short for call in calls)}")
