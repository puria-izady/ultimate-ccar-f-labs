"""The validator pattern every field check in the shop follows.

A validator is a class with a `field` attribute and a `check(value)` method. `check` returns
None when the value is acceptable, or a short message saying what is wrong. Validators never
raise for a bad value: the caller collects the messages and decides what to do with them.
"""


class Validator:
    field = ""

    def check(self, value):
        raise NotImplementedError

    def __repr__(self):
        return f"<{type(self).__name__} field={self.field!r}>"


def run_validators(record: dict, validators) -> dict:
    """Return {field: message} for every validator that rejects its field's value."""
    problems = {}
    for validator in validators:
        message = validator.check(record.get(validator.field))
        if message is not None:
            problems[validator.field] = message
    return problems
