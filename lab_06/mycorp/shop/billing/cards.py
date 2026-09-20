"""Card operations. Every function here goes on to the payments gateway."""
from shop.money import TAX_RATE
from shop.payments.gateway import GatewayClient


def charge_card(card_token: str, amount: float, currency: str = "GBP", client=None) -> dict:
    """Take a payment. The caller supplies an idempotency key through the gateway client."""
    client = client or GatewayClient()
    return client.charge(card_token, amount, currency)


def refund_card(card_token: str, amount: float, client=None) -> dict:
    client = client or GatewayClient()
    return client.refund(card_token, amount)


def calculate_tax(amount: float, rate: float = TAX_RATE) -> float:
    return round(amount * rate, 2)
