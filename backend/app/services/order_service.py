from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from ..domain.delivery.geo import GeoPoint
from ..domain.delivery.routing import RouteProvider
from ..domain.delivery.tracking import CourierPosition, courier_position
from ..domain.errors import BusinessRuleError, NotFoundError
from ..domain.events.publisher import OrderEventPublisher
from ..domain.orders.permissions import Actor, OrderAccess, authorize, is_allowed
from ..domain.orders.states import OrderFacts, state_for
from ..domain.payments.factory import PaymentGatewayFactory
from ..models import DeliveryMethod, Order, OrderStatus, PaymentMethod, PaymentStatus, UserRole
from ..models.base import utcnow
from ..repositories import LoyaltyRepository, OrderRepository, PageResult
from .order_events import transition

# Statuses staff can set through the API, and the State action behind each.
# "accepted" comes only from payment confirmation, "cancelled" only from the
# cancel command (it also refunds points and payments).
ACTION_FOR_STATUS: dict[str, str] = {
    OrderStatus.PREPARING: "start_preparing",
    OrderStatus.READY_FOR_PICKUP: "mark_ready",
    OrderStatus.DELIVERING: "pick_up",
    OrderStatus.DELIVERED: "deliver",
}


def order_facts(order: Order) -> OrderFacts:
    return OrderFacts(is_pickup=order.delivery_method == DeliveryMethod.PICKUP)


def order_access(order: Order) -> OrderAccess:
    return OrderAccess(
        customer_id=order.customer_id,
        courier_id=order.courier_id,
        is_pickup=order.delivery_method == DeliveryMethod.PICKUP,
    )


@dataclass(frozen=True)
class Tracking:
    order: Order
    route: list[GeoPoint]
    # Only while the courier is on the way.
    courier: CourierPosition | None


def _as_utc(value: datetime) -> datetime:
    # SQLite returns naive datetimes; values are always stored in UTC.
    return value if value.tzinfo else value.replace(tzinfo=UTC)


class OrderService:
    """Reading orders with ownership rules, and moving them through their
    lifecycle: the `OrderState` decides if a move is possible, the permission
    policy decides who may make it, and the change is published to observers."""

    def __init__(
        self,
        orders: OrderRepository,
        events: OrderEventPublisher,
        routes: RouteProvider,
        loyalty: LoyaltyRepository,
        gateways: PaymentGatewayFactory,
        clock: Callable[[], datetime] = utcnow,
    ) -> None:
        self._orders = orders
        self._events = events
        self._routes = routes
        self._loyalty = loyalty
        self._gateways = gateways
        self._clock = clock

    def get_order(self, order_id: int, actor: Actor) -> Order:
        order = self._orders.get_with_details(order_id)
        # Someone else's order looks exactly like a missing one, so ids can't be probed.
        if order is None or not self._can_view(order, actor):
            raise NotFoundError("Order not found.", "ORDER_NOT_FOUND")
        return order

    def history(self, customer_id: int, page: int, per_page: int) -> PageResult[Order]:
        return self._orders.page_for_customer(customer_id, page, per_page)

    def available_transitions(self, order: Order, actor: Actor) -> list[str]:
        """Statuses this actor can move the order to right now (for UI buttons)."""
        access = order_access(order)
        return [
            next_state.status
            for action, next_state in state_for(order.status)
            .available_actions(order_facts(order))
            .items()
            if next_state.status in ACTION_FOR_STATUS and is_allowed(action, actor, access)
        ]

    def change_status(self, order_id: int, target: str, actor: Actor) -> Order:
        action = ACTION_FOR_STATUS.get(target)
        if action is None:
            raise BusinessRuleError(
                f"Status '{target}' can't be set directly.", "STATUS_NOT_SETTABLE", field="status"
            )
        # Locked so two staff members can't move the same order at once.
        order = self._orders.get_with_details(order_id, for_update=True)
        if order is None or not self._can_view(order, actor):
            raise NotFoundError("Order not found.", "ORDER_NOT_FOUND")

        authorize(action, actor, order_access(order))
        next_state = state_for(order.status).apply(action, order_facts(order))

        if action == "pick_up":
            self._start_ride(order)
        if action == "deliver" and order.payment_method == PaymentMethod.CASH:
            self._mark_cash_paid(order)
        transition(self._events, order, next_state.status, changed_by_id=actor.user_id)
        self._orders.commit()
        return order

    def can_cancel(self, order: Order, actor: Actor) -> bool:
        return "cancel" in state_for(order.status).available_actions(
            order_facts(order)
        ) and is_allowed("cancel", actor, order_access(order))

    def cancel(self, order_id: int, actor_user_id: int, actor_role: str) -> Order:
        """Receiver of `CancelOrderCommand`.

        Everything happens in one transaction: the State transition, giving back
        spent points, refunding a paid online payment and publishing the change.
        If the refund fails, the order stays as it was.
        """
        actor = Actor(user_id=actor_user_id, role=actor_role)
        order = self._orders.get_with_details(order_id, for_update=True)
        if order is None or not self._can_view(order, actor):
            raise NotFoundError("Order not found.", "ORDER_NOT_FOUND")
        authorize("cancel", actor, order_access(order))
        next_state = state_for(order.status).apply("cancel", order_facts(order))
        try:
            self._refund_points(order)
            self._refund_payments(order)
            transition(self._events, order, next_state.status, changed_by_id=actor_user_id)
            self._orders.commit()
        except Exception:
            self._orders.rollback()
            raise
        return order

    def _refund_points(self, order: Order) -> None:
        if order.bonus_points_used == 0:
            return
        account = self._loyalty.get_account(order.customer_id, for_update=True)
        if account is not None:
            account.refund_points(order.bonus_points_used, order)

    def _refund_payments(self, order: Order) -> None:
        for payment in order.payments:
            if payment.status != PaymentStatus.PAID or payment.external_id is None:
                continue
            gateway = self._gateways.for_provider(payment.provider)
            gateway.refund(payment.external_id, payment.amount)
            payment.status = PaymentStatus.REFUNDED
            order.payment_status = PaymentStatus.REFUNDED

    def tracking(self, order_id: int, actor: Actor) -> Tracking:
        """Route and simulated courier position, recomputed on every request."""
        order = self.get_order(order_id, actor)
        route = [GeoPoint(lat, lng) for lat, lng in order.route or []]
        courier = None
        if order.status == OrderStatus.DELIVERING and route and order.picked_up_at:
            courier = courier_position(route, _as_utc(order.picked_up_at), self._clock())
        return Tracking(order=order, route=route, courier=courier)

    def _start_ride(self, order: Order) -> None:
        """Stores the road route (OSRM, or a straight line if it's unavailable)
        and the pick-up time; positions are interpolated from these later."""
        if order.delivery_lat is None or order.delivery_lng is None:
            raise BusinessRuleError("This order has no delivery point.", "DELIVERY_POINT_MISSING")
        route = self._routes.route(
            GeoPoint(order.restaurant.lat, order.restaurant.lng),
            GeoPoint(order.delivery_lat, order.delivery_lng),
        )
        order.route = [[point.lat, point.lng] for point in route.points]
        order.picked_up_at = self._clock()

    @staticmethod
    def _mark_cash_paid(order: Order) -> None:
        """Cash is collected when the order is handed over."""
        now = utcnow()
        order.payment_status = PaymentStatus.PAID
        for payment in order.payments:
            if payment.status == PaymentStatus.PENDING:
                payment.status = PaymentStatus.PAID
                payment.paid_at = now

    @staticmethod
    def _can_view(order: Order, actor: Actor) -> bool:
        if actor.role == UserRole.ADMIN:
            return True
        if actor.role == UserRole.COURIER:
            # Couriers see their own orders and the ones waiting for any courier.
            waiting_for_courier = (
                order.courier_id is None
                and order.status == OrderStatus.READY_FOR_PICKUP
                and order.delivery_method != DeliveryMethod.PICKUP
            )
            return order.courier_id == actor.user_id or waiting_for_courier
        return order.customer_id == actor.user_id
