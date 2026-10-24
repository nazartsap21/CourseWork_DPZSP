from dataclasses import dataclass, replace

from ..domain.events.publisher import OrderEventPublisher
from ..domain.orders.states import initial_state
from ..domain.orders.validation import OrderValidationError
from ..models import Order
from ..repositories import LoyaltyRepository, OrderRepository
from .order_events import publish_status
from .payment_service import PaymentService
from .quote_service import OrderQuoteService, QuoteRequest


@dataclass(frozen=True)
class CheckoutRequest:
    quote: QuoteRequest
    payment_method: str


@dataclass(frozen=True)
class CheckoutResult:
    order: Order
    # Where to send the customer to pay; None when nothing has to be paid now (cash).
    payment_redirect_url: str | None


class CheckoutFacade:
    """Facade: the single entry point for placing an order.

    Behind `place_order` several subsystems cooperate: `OrderBuilder` assembles
    the draft, the `OrderValidator` chain checks it, a `DeliveryStrategy` and the
    `PriceComponent` decorators price it (all via `OrderQuoteService`), the
    `PaymentGatewayFactory` picks a `PaymentGateway`, the `OrderState` decides the
    initial status, repositories persist the order, its payment and the spent
    points, and the `OrderEventPublisher` tells observers, all in one
    transaction. The API layer calls only this method.
    """

    def __init__(
        self,
        quotes: OrderQuoteService,
        orders: OrderRepository,
        loyalty: LoyaltyRepository,
        payments: PaymentService,
        events: OrderEventPublisher,
    ) -> None:
        self._quotes = quotes
        self._orders = orders
        self._loyalty = loyalty
        self._payments = payments
        self._events = events

    def place_order(self, request: CheckoutRequest, customer_id: int) -> CheckoutResult:
        # Resolve the gateway first: without a Stripe key "stripe" becomes the mock,
        # and the order must record the provider that really takes the money.
        gateway = self._payments.gateway_for(request.payment_method)
        quote = self._quotes.quote(
            replace(request.quote, payment_method=gateway.provider), customer_id
        )
        # The quote only reports broken rules; placing an order enforces them.
        if quote.validation_error is not None:
            raise quote.validation_error

        state = initial_state(pays_online=gateway.is_online)
        try:
            order = self._orders.create_from_draft(
                quote.draft,
                quote.price,
                status=state.status,
                estimated_delivery_minutes=quote.delivery.eta_minutes_max,
            )
            # Observers write the first history row and the "accepted" notification.
            publish_status(self._events, order, old_status=None, changed_by_id=customer_id)
            self._spend_points(customer_id, order)
            # Inside the transaction: if the provider fails, no unpaid order is left behind.
            redirect_url = self._payments.start(order, gateway)
            self._orders.commit()
        except Exception:
            self._orders.rollback()
            raise
        return CheckoutResult(order=order, payment_redirect_url=redirect_url)

    def _spend_points(self, customer_id: int, order: Order) -> None:
        if order.bonus_points_used == 0:
            return
        # Re-read the balance under a row lock: another checkout may have spent
        # points between the quote and now.
        account = self._loyalty.get_account(customer_id, for_update=True)
        if account is None or account.points_balance < order.bonus_points_used:
            raise OrderValidationError(
                "Your points balance changed. Check the order and try again.",
                "NOT_ENOUGH_POINTS",
                field="bonus_points",
            )
        account.redeem(order.bonus_points_used, order)
