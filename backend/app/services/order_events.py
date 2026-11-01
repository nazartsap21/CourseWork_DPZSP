"""The one way services change an order's status: apply it, then publish it.

Observers (history, notifications, loyalty) react to the event, so the
services that move orders stay unaware of them.
"""

from ..domain.events.publisher import OrderEventPublisher, OrderStatusChanged
from ..models import DeliveryMethod, Order
from ..models.base import utcnow


def publish_status(
    publisher: OrderEventPublisher,
    order: Order,
    old_status: str | None,
    changed_by_id: int | None,
) -> None:
    publisher.publish(
        OrderStatusChanged(
            order_id=order.id,
            customer_id=order.customer_id,
            total=order.total,
            restaurant_name=order.restaurant.name,
            is_pickup=order.delivery_method == DeliveryMethod.PICKUP,
            old_status=old_status,
            new_status=order.status.value,
            changed_by_id=changed_by_id,
            occurred_at=utcnow(),
        )
    )


def transition(
    publisher: OrderEventPublisher, order: Order, new_status: str, changed_by_id: int | None
) -> None:
    """Applies a status the `OrderState` already approved and announces it."""
    old_status = order.status.value
    order.change_status(new_status)
    publish_status(publisher, order, old_status, changed_by_id)
