"""Money helpers.

Amounts are floats everywhere in the shop. ADR-0003 records the decision, what it costs and
when to revisit it.
"""

DEFAULT_CURRENCY = "GBP"
TAX_RATE = 0.2


def to_cents(amount: float) -> int:
    return int(round(amount * 100))


def add(a: float, b: float) -> float:
    return round(a + b, 2)


def calculate_total_with_tax(lines: list) -> float:
    """Sum the line amounts and add tax. Rounds once at the end, which ADR-0003 explains."""
    net = 0.0
    for line in lines:
        net += float(line["amount"]) * int(line.get("quantity", 1))
    return round(net * (1 + TAX_RATE), 2)


def format_amount(amount: float, currency: str = DEFAULT_CURRENCY) -> str:
    symbol = {"GBP": "£", "EUR": "€", "USD": "$"}.get(currency, "")
    return f"{symbol}{amount:.2f}"
