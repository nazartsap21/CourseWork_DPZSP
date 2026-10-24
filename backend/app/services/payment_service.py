from dataclasses import dataclass

from ..domain.errors import BusinessRuleError, NotFoundError
from ..domain.orders.states import state_for
from ..domain.payments.factory import PaymentGatewayFactory
from ..domain.payments.gateways import SESSION_ID_PLACEHOLDER, PaymentGateway, PaymentRequest
from ..models import Order, OrderStatus, Payment, PaymentPurpose, PaymentStatus
from ..models.base import utcnow
from ..repositories import OrderRepository, PaymentRepository
from .order_service import order_facts


@dataclass(frozen=True)
class ReturnUrls:
    """Where the provider sends the customer back; `success` holds the session placeholder."""

    success: str
    cancel: str

    @classmethod
    def for_frontend(cls, frontend_url: str) -> "ReturnUrls":
        base = frontend_url.rstrip("/")
        return cls(
            success=f"{base}/checkout/success?session_id={SESSION_ID_PLACEHOLDER}",
            cancel=f"{base}/checkout/cancel?order_id={{order_id}}",
        )


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
    ) -> None:
        self._gateways = gateways
        self._payments = payments
        self._orders = orders
        self._return_urls = return_urls

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
                order_id=order.id,
                amount=order.total,
                description=f"Forkful order #{order.id} · {order.restaurant.name}",
                customer_email=order.customer.email,
                success_url=self._return_urls.success,
                cancel_url=self._return_urls.cancel.format(order_id=order.id),
            )
        )
        payment.external_id = session.external_id
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

    def confirm(self, external_id: str, customer_id: int) -> Order:
        """Checks the payment with its provider; if paid, moves the order on.

        Idempotent: returning to the success page twice doesn't pay twice.
        """
        payment = self._payments.get_by_external_id(external_id)
        if payment is None or payment.customer_id != customer_id or payment.order is None:
            raise NotFoundError("Payment not found.", "PAYMENT_NOT_FOUND")
        order = payment.order
        if payment.status == PaymentStatus.PAID:
            return order

        verification = self._gateways.for_provider(payment.provider).verify(external_id)
        if not verification.is_paid:
            raise BusinessRuleError(
                "The payment hasn't gone through. You can try again.", "PAYMENT_NOT_COMPLETED"
            )
        if verification.amount is not None and verification.amount != payment.amount:
            raise BusinessRuleError(
                "The paid amount doesn't match the order.", "PAYMENT_AMOUNT_MISMATCH"
            )

        # State pattern decides whether "paid" is a valid move from the current status.
        next_state = state_for(order.status).pay(order_facts(order))
        payment.status = PaymentStatus.PAID
        payment.paid_at = utcnow()
        order.payment_status = PaymentStatus.PAID
        order.change_status(next_state.status, changed_by_id=None)
        self._payments.commit()
        return order
