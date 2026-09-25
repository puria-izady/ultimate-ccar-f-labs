"""Client for the external payments gateway.

This is the only module in the shop that opens a network connection. Anything that reaches it
in a test is a test that needs the gateway to be up, which is why the refund tests take a
gateway object rather than making one (ADR-0005).
"""
import json
import urllib.request

BASE_URL = "https://gateway.mycorp-payments.example/v2"


class GatewayTimeout(Exception):
    """The gateway did not answer in time. ADR-0005 says a bounded retry is the response."""


class GatewayRefused(Exception):
    """The gateway declined. ADR-0005 says this is a decision, not a failure: never retry it."""


class GatewayClient:
    """Talks to the payments gateway over HTTP."""

    def __init__(self, base_url: str = BASE_URL, api_key: str = "") -> None:
        self.base_url = base_url
        self.api_key = api_key

    def _post(self, path: str, payload: dict, timeout_seconds: float) -> dict:
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
        )
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))

    def charge(self, card_token: str, amount: float, currency: str = "GBP") -> dict:
        timeout_seconds = 5.0
        return self._post("/charges", {"card_token": card_token, "amount": amount,
                                       "currency": currency}, timeout_seconds)

    def refund(self, card_token: str, amount: float) -> dict:
        timeout_seconds = 5.0
        return self._post("/refunds", {"card_token": card_token, "amount": amount},
                          timeout_seconds)

    def reverse(self, charge_id: str) -> dict:
        return self._post("/reversals", {"charge_id": charge_id}, 20.0)
