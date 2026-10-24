from ..domain.errors import BusinessRuleError, ConflictError, NotFoundError
from ..models import DeliveryMethod, Order, OrderStatus
from ..repositories import OrderRepository


class CourierService:
    """The courier workspace: orders waiting for a courier, the courier's own
    deliveries, and taking an order. Picking up and delivering are status
    changes and go through `OrderService.change_status` like any other."""

    def __init__(self, orders: OrderRepository) -> None:
        self._orders = orders

    def available(self) -> list[Order]:
        return self._orders.list_waiting_for_courier()

    def active(self, courier_id: int) -> list[Order]:
        return self._orders.list_active_for_courier(courier_id)

    def take(self, order_id: int, courier_id: int) -> Order:
        """Assigns a ready courier order to this courier. The status doesn't change:
        the order stays `ready_for_pickup` until the courier picks it up."""
        # Locked: two couriers tapping "Take order" at once can't both get it.
        order = self._orders.get_with_details(order_id, for_update=True)
        if order is None or order.delivery_method == DeliveryMethod.PICKUP:
            raise NotFoundError("Order not found.", "ORDER_NOT_FOUND")
        if order.courier_id == courier_id:
            return order
        if order.courier_id is not None:
            raise ConflictError("Another courier has taken this order.", "ORDER_ALREADY_TAKEN")
        if order.status != OrderStatus.READY_FOR_PICKUP:
            raise BusinessRuleError("This order isn't ready for a courier.", "ORDER_NOT_READY")
        order.courier_id = courier_id
        self._orders.commit()
        return order
