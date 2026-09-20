"""Nightly job: retry the charges that failed during the day.

This one calls the billing function under its original name rather than the billing alias,
which is why a search for the alias alone misses it.
"""
from shop.billing.cards import charge_card


def retry_failed_charges(failures: list) -> list:
    results = []
    for failure in failures:
        results.append(charge_card(failure["card_token"], failure["amount"],
                                   failure.get("currency", "GBP")))
    return results
