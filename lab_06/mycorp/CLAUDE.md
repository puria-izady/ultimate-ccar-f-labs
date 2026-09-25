# MyCorp shop: working notes

The refund path of the MyCorp online shop: the payments gateway, refunds, the validators and
the money helpers they share. Seven modules, two decision records and a thin test suite.

## Conventions

- **Validators** follow the pattern in `shop/validators/__init__.py`: a class with a `field`
  attribute and a `check(value)` method returning `None` when the value is acceptable, or a
  short message saying what is wrong. A validator never raises for a bad value.
- **The gateway is the only network boundary.** `shop/gateway.py` opens connections; nothing
  else does. So the refund functions take a gateway object rather than making one, and
  anything that reaches it in a test is a test that needs the gateway to be up.
- **Retries** follow `docs/adr/ADR-0005-payment-gateway-retries.md`: a bounded retry on a
  timeout, never on a refusal.
- **Grep and Glob before Read.** Find the entry point by content, then follow the imports.
  Reading every file to answer one question is the failure this rule names, and it stays the
  failure however small the project is.
- **When asked for tests only, write the test file and stop.** Do not touch the module under
  test, and do not implement anything to make the tests pass.

## Running things

```bash
python -m pytest            # from this directory; conftest.py puts `shop` on the path
```

## Findings

Long investigations write what they learn to `notes/investigation.md` and read it back rather
than trusting what is still in the window. That file is prose, for a person to re-read.

`state/manifest.json` is the other half, and it is not prose: which phase is done, which files
that phase actually read, and the commit the run started from. Whether a finding still stands
is then arithmetic against `git diff --name-only`, rather than a judgement about how long ago
something was read. Keep its shape exactly as it is; add facts, never fields.
