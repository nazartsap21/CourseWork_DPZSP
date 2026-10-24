from ..domain.errors import NotFoundError
from ..models import Order, UserRole
from ..repositories import OrderRepository


class OrderService:
    """Read access to orders with ownership rules. Status changes join it later."""

    def __init__(self, orders: OrderRepository) -> None:
        self._orders = orders

    def get_order(self, order_id: int, user_id: int, role: str) -> Order:
        order = self._orders.get_with_details(order_id)
        # Someone else's order looks exactly like a missing one, so ids can't be probed.
        if order is None or not self._can_view(order, user_id, role):
            raise NotFoundError("Order not found.", "ORDER_NOT_FOUND")
        return order

    @staticmethod
    def _can_view(order: Order, user_id: int, role: str) -> bool:
        if role == UserRole.ADMIN:
            return True
        if role == UserRole.COURIER:
            return order.courier_id == user_id
        return order.customer_id == user_id
