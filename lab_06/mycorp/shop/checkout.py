"""Checkout: validate the order, then take the payment."""
from shop.billing import process_payment
from shop.money import add, calculate_total_with_tax
from shop.validators import run_validators
from shop.validators.refund_amount import RefundAmountValidator

VALIDATORS = [RefundAmountValidator()]


def place_order(order: dict, card_token: str) -> dict:
    total = calculate_total_with_tax(order["lines"])
    receipt = process_payment(card_token, total, order.get("currency", "GBP"))
    return {"status": "placed", "total": add(total, 0.0), "receipt": receipt}


def check_refund_request(request: dict) -> dict:
    """Run the refund validators over a request before it reaches the refunds service."""
    problems = run_validators(request, VALIDATORS)
    return {"status": "rejected", "problems": problems} if problems else {"status": "accepted"}
