from dataclasses import dataclass, replace

from ..domain.orders.states import initial_state
from ..domain.orders.validation import OrderValidationError
from ..models import Order, PaymentMethod
from ..repositories import LoyaltyRepository, OrderRepository
from .quote_service import OrderQuoteService, QuoteRequest


@dataclass(frozen=True)
class CheckoutRequest:
    quote: QuoteRequest
    payment_method: str


class CheckoutFacade:
    """Facade: the single entry point for placing an order.

    Behind `place_order` several subsystems cooperate: `OrderBuilder` assembles
    the draft, the `OrderValidator` chain checks it, a `DeliveryStrategy` and the
    `PriceComponent` decorators price it (all via `OrderQuoteService`), the
    `OrderState` decides the initial status, and repositories persist the order
    and spend the points in one transaction. The API layer calls only this
    method and knows none of those classes.
    """

    def __init__(
        self,
        quotes: OrderQuoteService,
        orders: OrderRepository,
        loyalty: LoyaltyRepository,
    ) -> None:
        self._quotes = quotes
        self._orders = orders
        self._loyalty = loyalty

    def place_order(self, request: CheckoutRequest, customer_id: int) -> Order:
        quote = self._quotes.quote(
            replace(request.quote, payment_method=request.payment_method), customer_id
        )
        # The quote only reports broken rules; placing an order enforces them.
        if quote.validation_error is not None:
            raise quote.validation_error

        state = initial_state(pays_online=request.payment_method != PaymentMethod.CASH)
        try:
            order = self._orders.create_from_draft(
                quote.draft,
                quote.price,
                status=state.status,
                estimated_delivery_minutes=quote.delivery.eta_minutes_max,
                created_by_id=customer_id,
            )
            self._spend_points(customer_id, order)
            self._orders.commit()
        except Exception:
            self._orders.rollback()
            raise
        return order

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
