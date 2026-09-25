# ADR-0005: Retries against the payments gateway

- Status: accepted
- Date: 2026-03-12
- Services: refunds-api, payments-gateway

## Decision

A timeout against the gateway is retried a bounded number of times with a short delay. A refusal
is never retried: a refused refund is a decision, not a failure. Every attempt carries the same
idempotency key.

## Why

The gateway times out on roughly one call in fifty during the evening peak (TKT-0044). Without a
retry those refunds fail in front of a customer; with an unbounded retry a slow gateway turns
into a queue of duplicate attempts.

## What it costs

A retry that reuses an idempotency key but presents a new request id has charged a customer
twice before now. The retry count lives in `shop/refunds.py` and appears once per function
there, so a change has to be made in each place rather than once.
