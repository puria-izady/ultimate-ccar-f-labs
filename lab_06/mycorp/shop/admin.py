"""Admin panel actions. Still on the legacy alias, see TKT-0036."""
from shop.legacy import compute_vat, take_payment


def charge_manually(card_token: str, amount: float, note: str = "") -> dict:
    receipt = take_payment(card_token, amount)
    return {"receipt": receipt, "tax": compute_vat(amount), "note": note}
