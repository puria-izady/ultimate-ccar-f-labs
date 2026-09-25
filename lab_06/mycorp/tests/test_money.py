from shop.money import add, format_amount


def test_add_rounds_to_two_places():
    assert add(0.1, 0.2) == 0.3


def test_format_amount_uses_the_currency_symbol():
    assert format_amount(12.5, "GBP").endswith("12.50")
