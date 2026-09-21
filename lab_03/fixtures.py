"""The Northwind support data the four tools serve.

None of this is Claude specific and none of it is the lesson, so it lives beside the
notebook rather than inside it. Read it if you want to know why a particular
conversation goes the way it does; two things in here are deliberate traps.

The dates are built relative to today rather than written down, because the thirty day
refund window has to keep meaning something however long after we wrote this you run
it. That is also why these are builders rather than a checked-in JSON file.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

__all__ = ["build", "STATUS_CODES", "POLICY"]

STATUS_CODES = {"placed": 10, "dispatched": 20, "delivered": 30, "returned": 40,
                "cancelled": 50}

POLICY = """\
# Support policy

- Refunds may be processed within **30 days** of delivery. Outside that window, offer a
  replacement or store credit.
- Price adjustments apply to **our own site only**, when the price drops within 14 days of
  purchase.
- An agent may refund up to **500 pounds**. Anything above that goes to a human.
- Damaged or faulty goods are replaced free of charge inside the refund window.
"""


def _days_ago(n: int) -> datetime:
    return (datetime.now(timezone.utc) - timedelta(days=n)).replace(microsecond=0)


def _unix(n: int) -> int:
    return int(_days_ago(n).timestamp())


def _customers() -> list[dict]:
    # get_customer answers with Unix timestamps. lookup_order answers with ISO 8601 and a
    # numeric status code. Same concepts, two shapes: that is what the normaliser removes.
    # Trap: CUST-0023 and CUST-0031 share the name Sam Okafor.
    rows = [
        ("CUST-0001", "Ivan Petrov", "ivan.petrov@example.com", "07700900001", "standard", 420, 2),
        ("CUST-0007", "Ada Whitfield", "ada.whitfield@example.com", "07700900007", "standard", 300, 70),
        ("CUST-0011", "Marek Nowak", "marek.nowak@example.com", "07700900011", "premium", 210, 9),
        ("CUST-0017", "Leah Mensah", "leah.mensah@example.com", "07700900017", "standard", 150, 4),
        ("CUST-0023", "Sam Okafor", "sam.okafor@example.com", "07700900023", "standard", 95, 30),
        ("CUST-0031", "Sam Okafor", "s.okafor@example.net", "07700900031", "premium", 60, 11),
    ]
    return [
        {"customer_id": cid, "name": name, "email": email, "phone": phone, "tier": tier,
         "created": _unix(created), "last_contact_at": _unix(contacted)}
        for cid, name, email, phone, tier, created, contacted in rows
    ]


def _order(order_id, customer_id, total_pence, delivered, item, sku, shipment, invoice) -> dict:
    """A verbose backend record. Thirty-three fields arrive; five decide a refund."""
    return {
        "order_id": order_id, "customer_id": customer_id,
        "status": STATUS_CODES["delivered"], "status_detail": "left with resident",
        "placed_at": _days_ago(delivered + 3).isoformat(),
        "dispatched_at": _days_ago(delivered + 1).isoformat(),
        "delivered_at": _days_ago(delivered).isoformat(),
        "updated_at": _days_ago(delivered).isoformat(),
        "currency": "GBP", "subtotal_pence": total_pence - 499, "shipping_pence": 499,
        "tax_pence": round(total_pence / 6), "total_pence": total_pence, "discount_pence": 0,
        "refunded_pence": 0, "payment_method": "card",
        "payment_reference": "PAY-" + order_id[-4:],
        "invoice_id": invoice, "shipment_id": shipment, "carrier": "Northbound Logistics",
        "tracking_url": "https://tracking.example.com/" + shipment, "warehouse": "LEE-2",
        "channel": "web", "locale": "en-GB", "item_sku": sku, "item_name": item,
        "item_quantity": 1, "item_unit_pence": total_pence - 499, "gift_wrap": False,
        "marketing_source": "organic", "weight_grams": 1450, "return_window_days": 30,
        "signature_required": False,
    }


def _orders() -> list[dict]:
    # ORD-0009 was delivered 67 days ago, which is what puts it outside the refund window.
    return [
        _order("ORD-0003", "CUST-0001", 8999, 18, "Ridgeline walking boots", "SKU-441", "SHP-0004", "INV-0002"),
        _order("ORD-0021", "CUST-0001", 65000, 10, "Aurora espresso machine", "SKU-902", "SHP-0022", "INV-0020"),
        _order("ORD-0009", "CUST-0007", 12000, 67, "Cormorant rain shell", "SKU-118", "SHP-0010", "INV-0008"),
        _order("ORD-0014", "CUST-0011", 21000, 6, "Harrow cast iron set", "SKU-655", "SHP-0015", "INV-0013"),
        _order("ORD-0019", "CUST-0017", 6450, 8, "Tamar wool jumper", "SKU-207", "SHP-0020", "INV-0018"),
    ]


def _invoices() -> list[dict]:
    # INV-0002 is the duplicate charge from the Chapter 9 slide: the same amount, twice.
    return [
        {"invoice_id": "INV-0002", "customer_id": "CUST-0001", "order_id": "ORD-0003",
         "amount_pence": 4000, "charges": 2, "charged_at": _days_ago(17).isoformat()},
        {"invoice_id": "INV-0020", "customer_id": "CUST-0001", "order_id": "ORD-0021",
         "amount_pence": 65000, "charges": 1, "charged_at": _days_ago(11).isoformat()},
    ]


def build(workspace: Path) -> Path:
    """Write the data the tools read, and the policy the agent is measured against."""
    data = Path(workspace) / "data"
    data.mkdir(parents=True, exist_ok=True)
    tables = {"customers": _customers(), "orders": _orders(), "invoices": _invoices()}
    for name, rows in tables.items():
        (data / f"{name}.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    (Path(workspace) / "policy.md").write_text(POLICY, encoding="utf-8")

    print(f"{len(tables['customers'])} customers, two of them sharing a name")
    print(f"{len(tables['orders'])} orders, {len(tables['orders'][0])} fields each, "
          f"{len(tables['invoices'])} invoices")
    print("policy.md: 30 day window, own site only, 500 pound agent limit, "
          "and nothing at all about competitors")
    return data
