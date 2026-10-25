from dataclasses import dataclass
from datetime import datetime

from ..domain.errors import BusinessRuleError, NotFoundError
from ..domain.events.publisher import OrderEventPublisher
from ..domain.orders.states import state_for
from ..domain.payments.factory import PaymentGatewayFactory
from ..domain.payments.gateways import SESSION_ID_PLACEHOLDER, PaymentGateway, PaymentRequest
from ..models import (
    LoyaltyAccount,
    Order,
    OrderStatus,
    Payment,
    PaymentPurpose,
    PaymentStatus,
)
from ..models.base import utcnow
from ..repositories import LoyaltyRepository, OrderRepository, PaymentRepository
from .order_events import transition
from .order_service import order_facts


@dataclass(frozen=True)
class ReturnUrls:
    """Where the provider sends the customer back; `success` holds the session placeholder."""

    success: str
    cancel: str
    premium_cancel: str

    @classmethod
    def for_frontend(cls, frontend_url: str) -> "ReturnUrls":
        base = frontend_url.rstrip("/")
        return cls(
            success=f"{base}/checkout/success?session_id={SESSION_ID_PLACEHOLDER}",
            cancel=f"{base}/checkout/cancel?order_id={{order_id}}",
            premium_cancel=f"{base}/account?premium=cancelled",
        )


@dataclass(frozen=True)
class PaymentConfirmation:
    """What a confirmed payment was for: an order, or the premium card."""

    purpose: str
    order: Order | None = None
    premium_until: datetime | None = None


class PaymentService:
    """Starts and confirms order payments through whichever `PaymentGateway`
    the `PaymentGatewayFactory` provides. Never commits on its own when called
    from checkout, so the order and its payment are saved together."""

    def __init__(
        self,
        gateways: PaymentGatewayFactory,
        payments: PaymentRepository,
        orders: OrderRepository,
        return_urls: ReturnUrls,
        events: OrderEventPublisher,
        loyalty: LoyaltyRepository,
    ) -> None:
        self._gateways = gateways
        self._payments = payments
        self._orders = orders
        self._return_urls = return_urls
        self._events = events
        self._loyalty = loyalty

    def gateway_for(self, payment_method: str) -> PaymentGateway:
        return self._gateways.for_method(payment_method)

    def start(self, order: Order, gateway: PaymentGateway) -> str | None:
        """Creates a Payment row and starts the gateway session.

        Returns the URL the customer must visit to pay, or None (cash). Raises
        `PaymentProviderError` if the provider fails; the caller rolls back.
        """
        payment = Payment(
            customer_id=order.customer_id,
            order=order,
            purpose=PaymentPurpose.ORDER,
            provider=gateway.provider,
            amount=order.total,
            status=PaymentStatus.PENDING,
        )
        self._payments.add(payment)
        session = gateway.start(
            PaymentRequest(
                reference=f"order-{order.id}",
                amount=order.total,
                description=f"Forkful order #{order.id} · {order.restaurant.name}",
                customer_email=order.customer.email,
                success_url=self._return_urls.success,
                cancel_url=self._return_urls.cancel.format(order_id=order.id),
            )
        )
        payment.external_id = session.external_id
        return session.redirect_url

    def start_premium(
        self, account: LoyaltyAccount, customer_email: str, payment_method: str, price: int
    ) -> str:
        """Starts paying for the premium card: same gateways, a payment without an order."""
        gateway = self._gateways.for_method(payment_method)
        if not gateway.is_online:
            raise BusinessRuleError(
                "The premium card is paid online.",
                "PAYMENT_METHOD_UNAVAILABLE",
                field="payment_method",
            )
        payment = Payment(
            customer_id=account.customer_id,
            purpose=PaymentPurpose.PREMIUM_CARD,
            provider=gateway.provider,
            amount=price,
            status=PaymentStatus.PENDING,
        )
        self._payments.add(payment)
        try:
            self._payments.flush()
            session = gateway.start(
                PaymentRequest(
                    reference=f"premium-{payment.id}",
                    amount=price,
                    description="Forkful premium card · free delivery",
                    customer_email=customer_email,
                    success_url=self._return_urls.success,
                    cancel_url=self._return_urls.premium_cancel,
                )
            )
            payment.external_id = session.external_id
            self._payments.commit()
        except Exception:
            self._payments.rollback()
            raise
        if session.redirect_url is None:
            raise BusinessRuleError(
                "This payment method can't be used here.", "PAYMENT_METHOD_UNAVAILABLE"
            )
        return session.redirect_url

    def restart(self, order_id: int, customer_id: int) -> str:
        """New payment attempt for an order still waiting for payment (after a cancel)."""
        order = self._orders.get_with_details(order_id)
        if order is None or order.customer_id != customer_id:
            raise NotFoundError("Order not found.", "ORDER_NOT_FOUND")
        if order.status != OrderStatus.PENDING_PAYMENT:
            raise BusinessRuleError("This order doesn't need a payment.", "PAYMENT_NOT_NEEDED")
        try:
            redirect_url = self.start(order, self._gateways.for_method(order.payment_method))
            self._payments.commit()
        except Exception:
            self._payments.rollback()
            raise
        if redirect_url is None:
            raise BusinessRuleError("This order is paid in cash.", "PAYMENT_NOT_NEEDED")
        return redirect_url

    def confirm(self, external_id: str, customer_id: int) -> PaymentConfirmation:
        """Checks the payment with its provider; if paid, moves the order on or
        activates the premium card.

        Idempotent: returning to the success page twice doesn't pay twice.
        """
        payment = self._payments.get_by_external_id(external_id)
        if payment is None or payment.customer_id != customer_id:
            raise NotFoundError("Payment not found.", "PAYMENT_NOT_FOUND")
        if payment.status == PaymentStatus.PAID:
            return self._already_confirmed(payment)

        verification = self._gateways.for_provider(payment.provider).verify(external_id)
        if not verification.is_paid:
            raise BusinessRuleError(
                "The payment hasn't gone through. You can try again.", "PAYMENT_NOT_COMPLETED"
            )
        if verification.amount is not None and verification.amount != payment.amount:
            raise BusinessRuleError(
                "The paid amount doesn't match the order.", "PAYMENT_AMOUNT_MISMATCH"
            )

        payment.status = PaymentStatus.PAID
        payment.paid_at = utcnow()
        if payment.purpose == PaymentPurpose.PREMIUM_CARD:
            confirmation = self._activate_premium(payment)
        else:
            confirmation = self._accept_order(payment)
        self._payments.commit()
        return confirmation

    def _accept_order(self, payment: Payment) -> PaymentConfirmation:
        order = payment.order
        if order is None:
            raise NotFoundError("Payment not found.", "PAYMENT_NOT_FOUND")
        # State pattern decides whether "paid" is a valid move from the current status.
        next_state = state_for(order.status).pay(order_facts(order))
        order.payment_status = PaymentStatus.PAID
        transition(self._events, order, next_state.status, changed_by_id=None)
        return PaymentConfirmation(purpose=PaymentPurpose.ORDER, order=order)

    def _activate_premium(self, payment: Payment) -> PaymentConfirmation:
        account = self._loyalty.get_account(payment.customer_id, for_update=True)
        if account is None:
            raise NotFoundError("Loyalty account not found.", "LOYALTY_ACCOUNT_NOT_FOUND")
        days = self._loyalty.get_settings().premium_card_days
        until = account.extend_premium(days, utcnow())
        return PaymentConfirmation(purpose=PaymentPurpose.PREMIUM_CARD, premium_until=until)

    def _already_confirmed(self, payment: Payment) -> PaymentConfirmation:
        if payment.purpose == PaymentPurpose.PREMIUM_CARD:
            account = self._loyalty.get_account(payment.customer_id)
            return PaymentConfirmation(
                purpose=PaymentPurpose.PREMIUM_CARD,
                premium_until=account.premium_until if account else None,
            )
        return PaymentConfirmation(purpose=PaymentPurpose.ORDER, order=payment.order)
