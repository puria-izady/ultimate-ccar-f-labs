"""Currency conversion.

Every conversion asks the gateway for a rate, so a page that shows twenty prices makes twenty
calls. TKT-0052 asks for a cache in front of this; nothing caches yet.
"""
from shop.money import DEFAULT_CURRENCY


def convert(amount: float, quote: str, source, base: str = DEFAULT_CURRENCY) -> float:
    """Convert an amount from `base` into `quote`, asking `source` for the rate every time."""
    if quote == base:
        return round(amount, 2)
    return round(amount * source.exchange_rate(base, quote), 2)
