"""Our own payment interface. The rest of the app talks only to `PaymentGateway`;
concrete providers (cash, a mock for local runs, Stripe) plug in behind it, so
services depend on this abstraction rather than on any SDK (DIP, Protected
Variations)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import uuid4

from ..errors import ExternalServiceError

# Placeholder the provider replaces with the real session id in the return URL.
# The value is Stripe's own template variable; the mock gateway mimics it.
SESSION_ID_PLACEHOLDER = "{CHECKOUT_SESSION_ID}"


class PaymentProviderError(ExternalServiceError):
    """The external provider failed or refused (network, bad key). HTTP 502."""

    code = "PAYMENT_PROVIDER_ERROR"


@dataclass(frozen=True)
class PaymentRequest:
    """`amount` is integer kopiyky. `success_url` contains SESSION_ID_PLACEHOLDER.
    `reference` names what is paid for ("order-12", "premium-5"), for the provider's records."""

    reference: str
    amount: int
    description: str
    customer_email: str
    success_url: str
    cancel_url: str
    currency: str = "uah"


@dataclass(frozen=True)
class PaymentSession:
    """Result of starting a payment.

    `redirect_url` is where the customer must go to pay (None: nothing to do now).
    `external_id` identifies the payment at the provider (None for cash).
    """

    external_id: str | None
    redirect_url: str | None


@dataclass(frozen=True)
class PaymentVerification:
    is_paid: bool
    amount: int | None


class PaymentGateway(ABC):
    provider: str

    @property
    def is_online(self) -> bool:
        """Online payments must be confirmed before the kitchen starts."""
        return True

    @abstractmethod
    def start(self, request: PaymentRequest) -> PaymentSession: ...

    @abstractmethod
    def verify(self, external_id: str) -> PaymentVerification: ...

    @abstractmethod
    def refund(self, external_id: str, amount: int) -> None:
        """Returns a captured payment in full. Raises `PaymentProviderError` on failure."""


class CashGateway(PaymentGateway):
    """Cash on delivery or at pickup: nothing to start online, paid when handed over."""

    provider = "cash"

    @property
    def is_online(self) -> bool:
        return False

    def start(self, request: PaymentRequest) -> PaymentSession:
        return PaymentSession(external_id=None, redirect_url=None)

    def verify(self, external_id: str) -> PaymentVerification:
        return PaymentVerification(is_paid=False, amount=None)

    def refund(self, external_id: str, amount: int) -> None:
        # Nothing was taken online; cash orders can't be cancelled after handover.
        return None


class MockGateway(PaymentGateway):
    """Behaves like a successful card payment without any external service.

    It follows the same redirect → success page → verify flow as Stripe, so the
    full online path works locally when no Stripe key is configured.
    """

    provider = "mock"
    ID_PREFIX = "mock_"

    def start(self, request: PaymentRequest) -> PaymentSession:
        external_id = f"{self.ID_PREFIX}{request.reference}_{uuid4().hex[:12]}"
        return PaymentSession(
            external_id=external_id,
            redirect_url=request.success_url.replace(SESSION_ID_PLACEHOLDER, external_id),
        )

    def verify(self, external_id: str) -> PaymentVerification:
        return PaymentVerification(is_paid=external_id.startswith(self.ID_PREFIX), amount=None)

    def refund(self, external_id: str, amount: int) -> None:
        return None
