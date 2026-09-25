"""Validator for the amount on a refund request.

The gateway sends the amount back as a JSON string on the portal-initiated path, which is where
TKT-0053 comes from.
"""
from . import Validator

MAX_REFUND = 500.0


class RefundAmountValidator(Validator):
    field = "refund_amount"

    def check(self, value):
        if value is None:
            return "refund_amount is required"
        if value > MAX_REFUND:
            return f"refund_amount must be {MAX_REFUND:.2f} or less"
        if value <= 0:
            return "refund_amount must be greater than zero"
        return None
