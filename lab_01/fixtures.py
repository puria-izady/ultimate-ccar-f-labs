"""The Fernhill workspace the tools serve.

Nothing here is Claude specific. It is three tickets, a service catalogue, two
architecture decision records and three small Python files.

The Python files carry two deliberate traps, and part B collects on both. One function is
re-exported under two other names, so searching for the original name finds a third of the
callers. And one line appears twice, identically, which is what makes an edit anchor
ambiguous.
"""

from __future__ import annotations

import json
from pathlib import Path

__all__ = ["build", "TICKETS", "SERVICES"]

TICKETS = [
    {"id": "TKT-0042", "status": "open", "service": "refunds",
     "title": "Customers charged twice when a refund is retried",
     "body": "Two customers report duplicate charges after a refund was retried. "
             "The retry count in the refunds client looks wrong."},
    {"id": "TKT-0051", "status": "open", "service": "checkout",
     "title": "Order note validator rejects valid notes",
     "body": "Notes containing an apostrophe are rejected. Probably the validator base class."},
    {"id": "TKT-0038", "status": "closed", "service": "billing",
     "title": "Gateway timeouts during the Friday batch",
     "body": "Resolved by raising the gateway timeout. See ADR-0005."},
]

SERVICES = [
    {"name": "refunds", "owner": "Payments", "on_call": "Ada Okafor", "entrypoint": "shop/refunds.py"},
    {"name": "billing", "owner": "Payments", "on_call": "Ada Okafor", "entrypoint": "shop/billing.py"},
    {"name": "checkout", "owner": "Storefront", "on_call": "Nils Brandt", "entrypoint": "shop/legacy.py"},
]

_ADR_0003 = """\
# ADR-0003: Money is never a float

Status: accepted

Amounts are integers of pence, everywhere. Floats were the cause of three reconciliation
incidents in the first year. Any function that takes an amount takes `amount_pence: int`.
"""

_ADR_0005 = """\
# ADR-0005: The gateway is retried at most twice

Status: accepted

The payment gateway is retried on timeout, at most twice, with a delay between attempts.
Retrying more than that has caused duplicate charges, because the gateway may have
succeeded without us hearing about it.
"""

_BILLING = """\
# Card handling. The one place a card is actually charged.


def charge_card(order_id: str, amount_pence: int) -> dict:
    # Every payment in the shop ends up here.
    return {"order_id": order_id, "amount_pence": amount_pence, "status": "charged"}
"""

# Trap one, first hop: charge_card arrives here under a different name.
_LEGACY = """\
# Kept for the old admin panel. See ADR-0004.

from billing import charge_card as take_payment

__all__ = ["take_payment"]
"""

# Trap one, second hop, and trap two: max_retries = 3 appears twice, identically, so an
# Edit anchored on that line matches twice and fails.
_REFUNDS = """\
# Refund client.

from billing import charge_card as process_payment


def send_refund(order_id: str, amount_pence: int) -> dict:
    max_retries = 3
    return process_payment(order_id, -amount_pence)


def send_reversal(order_id: str, amount_pence: int) -> dict:
    max_retries = 3
    return process_payment(order_id, -amount_pence)
"""

FILES = {
    "data/tickets.json": json.dumps(TICKETS, indent=2),
    "data/services.json": json.dumps(SERVICES, indent=2),
    "data/adr/ADR-0003-money-as-floats.md": _ADR_0003,
    "data/adr/ADR-0005-payment-gateway-retries.md": _ADR_0005,
    "shop/billing.py": _BILLING,
    "shop/legacy.py": _LEGACY,
    "shop/refunds.py": _REFUNDS,
}


def build(workspace: Path) -> None:
    """Write the corpus and the code the tools and the agent work on."""
    for relative, body in FILES.items():
        path = Path(workspace) / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    print(f"{len(TICKETS)} tickets, {len(SERVICES)} services, 2 decision records, "
          f"3 Python files carrying two planted traps")


def reset_retry_count(workspace: Path) -> None:
    """Put the retry count back to 3, so part B's edit task still has work to do."""
    path = Path(workspace) / "shop" / "refunds.py"
    path.write_text(path.read_text().replace("max_retries = 5", "max_retries = 3"))
