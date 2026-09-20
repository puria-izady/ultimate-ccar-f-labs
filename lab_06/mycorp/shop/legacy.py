"""Compatibility shims for call sites that predate the billing rename (ADR-0004).

Nothing new should import from here. The names survive because one call site still uses them.
"""
from shop.billing import calculate_tax as compute_vat
from shop.billing import process_payment as take_payment

__all__ = ["take_payment", "compute_vat"]
