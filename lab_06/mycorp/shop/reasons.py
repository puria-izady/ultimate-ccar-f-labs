"""Reason codes on a refund.

The gateway sends the reason back in whatever form the merchant portal recorded it, and the
shop wants one canonical code. TKT-0051 asks for the transformation; nothing implements it yet.
"""

CANONICAL = ("damaged", "not_as_described", "late", "changed_mind", "other", "unknown")


def normalise_reason(raw):
    """Turn a gateway reason code into one of CANONICAL.

    TKT-0051. Not implemented: the ticket describes the rules in prose and the prose has already
    produced two different readings, so the next attempt should carry worked examples.
    """
    raise NotImplementedError("TKT-0051")
