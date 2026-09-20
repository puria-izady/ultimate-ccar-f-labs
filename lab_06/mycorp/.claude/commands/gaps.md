Map what the test suite covers and what it does not, for: $ARGUMENTS

Do it in this order.

1. Map the structure first: which modules exist, which have tests, which do not. Glob and Grep
   before Read.
2. Rank the untested areas by what a defect would cost, not by line count. Money and the
   gateway outrank formatting.
3. Produce a prioritised plan, worst gap first, with one line per item saying what the test
   would assert.
4. For each item, say whether a test can be written against the current signature or whether
   the code has to change first. When an item turns out to need the external gateway, say so
   and put the work of standing the gateway in before the tests that depend on it, rather than
   leaving the plan as it was.

Write nothing yet. The plan is the deliverable.
