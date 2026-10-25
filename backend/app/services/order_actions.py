from ..domain.orders.commands import (
    CancelOrderCommand,
    CommandInvoker,
    CurrentMenu,
    PastOrders,
    ReorderCommand,
    ReorderResult,
)
from ..domain.orders.permissions import Actor
from ..models import Order
from .order_service import OrderService


class OrderActions:
    """Command client: builds the command for a customer action and hands it
    to the `CommandInvoker`, which executes and logs it."""

    def __init__(
        self,
        invoker: CommandInvoker,
        orders: OrderService,
        past_orders: PastOrders,
        menu: CurrentMenu,
    ) -> None:
        self._invoker = invoker
        self._orders = orders
        self._past_orders = past_orders
        self._menu = menu

    def reorder(self, order_id: int, customer_id: int) -> ReorderResult:
        command = ReorderCommand(order_id, customer_id, self._past_orders, self._menu)
        return self._invoker.run(command, actor_id=customer_id)

    def cancel(self, order_id: int, actor: Actor) -> Order:
        command = CancelOrderCommand(order_id, actor.user_id, actor.role, self._orders)
        return self._invoker.run(command, actor_id=actor.user_id)
