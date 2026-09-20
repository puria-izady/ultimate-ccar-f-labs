"""TKT-0053. This test ships with the ticket and fails until the validator is fixed.

The portal-initiated refund path sends the amount as a JSON string. The validator pattern says a validator
returns a message for a value it will not accept and never raises, so this one is a bug in the
validator rather than in the caller.
"""
from shop.validators import run_validators
from shop.validators.refund_amount import RefundAmountValidator


def test_a_string_amount_is_rejected_with_a_message():
    message = RefundAmountValidator().check("12.50")
    assert message is not None
    assert "refund_amount" in message


def test_a_string_amount_does_not_escape_run_validators():
    problems = run_validators({"refund_amount": "12.50"}, [RefundAmountValidator()])
    assert list(problems) == ["refund_amount"]


def test_a_good_amount_is_still_accepted():
    assert RefundAmountValidator().check(12.5) is None
