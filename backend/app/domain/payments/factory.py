"""Factory Method: creates the gateway for a payment method.

Callers ask for "the gateway for `stripe`" and get a `PaymentGateway`; which
class that is depends on the configuration. Without a Stripe key, card payments
are served by `MockGateway`, so the project runs end to end without secrets.
"""

from collections.abc import Callable

from ..errors import BusinessRuleError
from .gateways import CashGateway, MockGateway, PaymentGateway


class PaymentGatewayFactory:
    def __init__(self, stripe_gateway: Callable[[], PaymentGateway] | None = None) -> None:
        # The Stripe gateway is built lazily, and only when a key is configured.
        self._creators: dict[str, Callable[[], PaymentGateway]] = {
            CashGateway.provider: CashGateway,
            MockGateway.provider: MockGateway,
            "stripe": stripe_gateway or MockGateway,
        }

    def for_method(self, payment_method: str) -> PaymentGateway:
        """Gateway for the method the customer chose (`stripe` may resolve to the mock)."""
        creator = self._creators.get(payment_method)
        if creator is None:
            raise BusinessRuleError(
                f"Payment method '{payment_method}' is not available.",
                "PAYMENT_METHOD_UNAVAILABLE",
                field="payment_method",
            )
        return creator()

    def for_provider(self, provider: str) -> PaymentGateway:
        """Gateway that handled an existing payment, to verify it."""
        return self.for_method(provider)
