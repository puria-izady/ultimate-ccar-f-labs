"""The refund flow, which reaches the payments gateway through a client it is given.

Retries follow ADR-0005: a bounded number of attempts on a timeout, and nothing at all on a
refusal, because a refused refund is a decision rather than a failure.

The customer is told nothing when a refund succeeds. ADR-0007 is the open question about
where that notification should come from, and the way out of `send_refund` is the seam.
"""
import time

from shop.gateway import GatewayRefused, GatewayTimeout


def send_refund(card_token: str, amount: float, gateway) -> dict:
    """Send one refund, retrying a timeout a bounded number of times."""
    retry_count = 3
    delay = 0.2
    for attempt in range(retry_count):
        try:
            return gateway.refund(card_token, amount)
        except GatewayTimeout:
            if attempt == retry_count - 1:
                raise
            time.sleep(delay)
        except GatewayRefused:
            raise
    raise GatewayTimeout("refund gave up")


def send_reversal(charge_id: str, gateway) -> dict:
    """Reverse a charge that was taken twice, retrying a timeout the same way."""
    retry_count = 3
    delay = 0.2
    for attempt in range(retry_count):
        try:
            return gateway.reverse(charge_id)
        except GatewayTimeout:
            if attempt == retry_count - 1:
                raise
            time.sleep(delay)
    raise GatewayTimeout("reversal gave up")
