"""The outbox the shop already uses for order confirmations.

A row written here is drained by `notifications-worker` every thirty seconds. Writing to it
is the second of the two designs ADR-0007 leaves open, so it is the thing that design has to
point at.
"""

_ROWS: list[dict] = []


def enqueue(topic: str, payload: dict) -> dict:
    """Append one row. Callers write inside the transaction that made the change."""
    row = {"topic": topic, "payload": payload, "sent": False}
    _ROWS.append(row)
    return row


def drain() -> list[dict]:
    """What the worker collects. Marks each row sent and returns it."""
    pending = [row for row in _ROWS if not row["sent"]]
    for row in pending:
        row["sent"] = True
    return pending
