# ADR-0003: Money as floats

- Status: accepted, with a known cost
- Date: 2025-11-04
- Services: billing-worker, orders-api

## Decision

Amounts stay Python floats, rounded to two places at the point a total is produced.

## Why

The shop launched against a gateway whose API took and returned floats, and the first release
had six weeks to ship. Decimal would have meant a conversion at every boundary: the gateway, the
finance export and the stored order records.

## What it costs

Tax on some lines is a penny under what the invoice shows, because rounding happens once at the
end rather than per line (TKT-0028). Anything that sums many lines drifts.

## When to revisit

If a second currency arrives, or if finance rejects an export over rounding. Both have now
happened: TKT-0055 opens the migration. It is mechanical but it touches every module that
carries an amount, including the gateway boundary where the wire format is still a JSON number,
so it wants planning rather than an afternoon.
