# TKT-0031: customer charged twice on a retried refund

- Status: blocked
- Raised: 2026-03-05
- Service: refunds-api
- Related: ADR-0005, TKT-0044

## What happened

On 2026-03-07 a refund for order ORD-7712 timed out against the gateway. The bounded retry in
`send_refund` reused the idempotency key but the gateway had already accepted the first attempt
under a different request id, so the customer was charged 48.60 GBP twice.

## What was done

The duplicate charge of 48.60 GBP was reversed on 2026-03-09 through `send_reversal`. The
customer was made whole the same day.

## Why it is blocked

Nothing in the shop generates the request id, so the retry cannot present the same one. Fixing
it means the gateway client owns the idempotency key for the whole attempt sequence rather than
the caller passing one in. That is a change to `shop/refunds/client.py` and to the gateway
client, and it is waiting on the gateway team confirming that a repeated request id is accepted
rather than rejected.
