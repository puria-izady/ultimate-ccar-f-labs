from shop.validators import run_validators
from shop.validators.refund_amount import MAX_REFUND, RefundAmountValidator


def test_a_missing_amount_is_rejected_with_a_message():
    assert RefundAmountValidator().check(None) == "refund_amount is required"


def test_an_amount_over_the_ceiling_is_rejected():
    message = RefundAmountValidator().check(MAX_REFUND + 1)
    assert message is not None
    assert "500" in message


def test_run_validators_collects_messages_by_field():
    problems = run_validators({"refund_amount": None}, [RefundAmountValidator()])
    assert list(problems) == ["refund_amount"]
