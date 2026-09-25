# ADR-0007: Telling a customer their refund has been sent

- Status: proposed, no decision taken
- Date: 2026-04-14
- Services: refunds-api, notifications-worker

## The need

TKT-0054: a customer whose refund succeeds is told nothing until the money appears, which is two
to five working days. Support takes about forty "where is my refund" contacts a week.

## Constraints

- A refund that has reached the gateway must be recorded as sent even if nothing can be
  delivered to the customer. The notification may never fail the refund.
- The shop already has an `outbox` table, written inside the order transaction and drained by
  `notifications-worker` every thirty seconds. It is used for order confirmations today.
- The refunds service has no worker of its own and no queue of its own.
- Support wants the customer contacted within a minute of the refund being accepted.

## What is undecided

Whether the refunds service sends the notification itself on the way out, or writes a row to the
existing outbox and lets the worker send it. Both fit the constraints and they fail differently.
No decision has been taken and there is no deadline; whoever picks this up decides, records the
two options and says why they chose the one they chose.
