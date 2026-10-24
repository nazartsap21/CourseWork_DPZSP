from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..domain.orders.builder import OrderDraft
from ..domain.pricing.decorators import PriceBreakdown
from ..models import (
    DeliveryMethod,
    Order,
    OrderItem,
    OrderStatus,
    OrderStatusHistory,
    PaymentMethod,
    PaymentStatus,
)
from .base import SqlAlchemyRepository


class OrderRepository(SqlAlchemyRepository):
    def create_from_draft(
        self,
        draft: OrderDraft,
        price: PriceBreakdown,
        status: str,
        estimated_delivery_minutes: int,
        created_by_id: int,
    ) -> Order:
        """The persistence boundary: turns the domain draft into ORM rows.

        Item name and price are copied from the draft's dish snapshots, so the
        order keeps what the customer actually bought even if the menu changes.
        """
        if draft.customer_id is None or draft.payment_method is None:
            raise ValueError("A placed order needs a customer and a payment method.")
        order = Order(
            customer_id=draft.customer_id,
            restaurant_id=draft.restaurant.id,
            status=OrderStatus(status),
            delivery_method=DeliveryMethod(draft.delivery.method),
            delivery_address=draft.delivery.address,
            delivery_note=draft.delivery.note,
            delivery_lat=draft.delivery.destination.lat if draft.delivery.destination else None,
            delivery_lng=draft.delivery.destination.lng if draft.delivery.destination else None,
            subtotal=price.subtotal,
            delivery_fee=price.delivery_fee,
            discount=price.discount,
            bonus_points_used=price.bonus_points_used,
            total=price.total,
            payment_method=PaymentMethod(draft.payment_method),
            payment_status=PaymentStatus.PENDING,
            estimated_delivery_minutes=estimated_delivery_minutes,
            items=[
                OrderItem(
                    dish_id=item.dish.id,
                    name=item.dish.name,
                    price=item.dish.price,
                    quantity=item.quantity,
                )
                for item in draft.items
            ],
            status_history=[
                OrderStatusHistory(status=OrderStatus(status), changed_by_id=created_by_id)
            ],
        )
        self._session.add(order)
        self._session.flush()
        return order

    def get_with_details(self, order_id: int) -> Order | None:
        return self._session.scalar(
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.items),
                selectinload(Order.status_history),
                selectinload(Order.restaurant),
            )
        )
