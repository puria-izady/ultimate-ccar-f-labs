# ADR-0004: Alias exports in billing

- Status: accepted
- Date: 2026-01-20
- Services: orders-api, refunds-api

## Decision

`shop/billing/__init__.py` re-exports the card functions under their historic names:
`charge_card` as `process_payment` and `refund_card` as `issue_refund`. `shop/legacy.py`
carries two further names, `take_payment` and `compute_vat`, for call sites older still.

## Why

The rename landed with the billing package split. Rewriting every call site at once would have
touched the checkout flow, the admin panel and the nightly jobs in one change, during the
Christmas freeze.

## What it costs

Tracing a caller means searching for the alias as well as the original name. A search for
`charge_card` alone misses the checkout flow, which imports `process_payment`, and the admin
panel, which imports `take_payment` from the second shim. List the exported names first, then
search for each.

## When to revisit

When the compatibility shim has no importers left. TKT-0036 tracks the last one.
