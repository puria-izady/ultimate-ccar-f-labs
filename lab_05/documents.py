"""The three supplier documents this lab extracts from.

Each one is here to break something specific later.

| Document | What it breaks |
|---|---|
| `INVOICE` | nothing. The well-behaved case every schema is written against |
| `RECEIPT` | prints no purchase order and no date, which section 5 needs |
| `CREDIT_NOTE` | gives two reasons, one real but off any sensible list and one genuinely ambiguous, which section 6 needs |

They are written into `workspace/docs/` rather than committed, so you can open them beside
the notebook and change them.
"""

from __future__ import annotations

from pathlib import Path

__all__ = ["build", "INVOICE", "RECEIPT", "CREDIT_NOTE"]

INVOICE = """\
NORTHWIND TIMBER SUPPLIES LTD
Unit 7, Brackley Trading Estate

INVOICE

Invoice number : INV-4471
Invoice date   : 14 March
Your order ref : PO-99812

Description                    Qty      Price
Oak board, 2.4m                 12     540.00
Pine batten, 3m                 40     180.00
Delivery                         1      35.00

                         Total due     755.00

Payment terms: 30 days net
"""

# No purchase order anywhere on it, and no date. Section 5 turns on both absences.
RECEIPT = """\
BRACKLEY BUILDERS MERCHANT
Till 3        Receipt 8802

2 x sealant cartridge           11.80
1 x brush set                    6.40
1 x dust sheet                   4.95

TOTAL                           23.15
CARD ****4417   APPROVED

Thank you for your custom
"""

# Line 1's reason is real and outside any sensible list. Line 2's is ambiguous.
CREDIT_NOTE = """\
NORTHWIND TIMBER SUPPLIES LTD

CREDIT NOTE CN-221
Raised against invoice INV-4471

Line 1   Oak board, 2.4m   x2        -90.00
         Reason: goodwill gesture, the delivery ran three days late

Line 2   Pine batten, 3m   x4        -18.00
         Reason: customer rang, could not say what was wrong with them

                    Total credited  -108.00
"""

_FILES = {"invoice-4471.txt": INVOICE, "receipt-8802.txt": RECEIPT,
          "credit-note-221.txt": CREDIT_NOTE}


def build(workspace: Path) -> dict[str, str]:
    """Write the documents and hand back their text, keyed by short name."""
    docs = Path(workspace) / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    for name, body in _FILES.items():
        (docs / name).write_text(body, encoding="utf-8")
    print(f"{len(_FILES)} documents in {docs.name}/: " + ", ".join(sorted(_FILES)))
    return {"invoice": INVOICE, "receipt": RECEIPT, "credit_note": CREDIT_NOTE}
