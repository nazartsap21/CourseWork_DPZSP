from sqlalchemy import Select, func, select
from sqlalchemy.orm import selectinload

from ..domain.orders.builder import OrderDraft
from ..domain.orders.commands import PastOrder, PastOrderItem
from ..domain.pricing.decorators import PriceBreakdown
from ..models import (
    DeliveryMethod,
    Order,
    OrderItem,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
)
from .base import PageResult, SqlAlchemyRepository


class OrderRepository(SqlAlchemyRepository):
    def create_from_draft(
        self,
        draft: OrderDraft,
        price: PriceBreakdown,
        status: str,
        estimated_delivery_minutes: int,
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
        )
        self._session.add(order)
        self._session.flush()
        return order

    def get_with_details(self, order_id: int, for_update: bool = False) -> Order | None:
        """`for_update` locks the order row until commit (status changes)."""
        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.items),
                selectinload(Order.status_history),
                selectinload(Order.restaurant),
            )
        )
        if for_update:
            stmt = stmt.with_for_update(of=Order)
        return self._session.scalar(stmt)

    def _with_courier_details(self) -> Select[tuple[Order]]:
        return select(Order).options(
            selectinload(Order.items),
            selectinload(Order.restaurant),
            selectinload(Order.customer),
        )

    def list_waiting_for_courier(self) -> list[Order]:
        """Courier orders that are ready and not taken yet, oldest first."""
        return list(
            self._session.scalars(
                self._with_courier_details()
                .where(
                    Order.status == OrderStatus.READY_FOR_PICKUP,
                    Order.courier_id.is_(None),
                    Order.delivery_method != DeliveryMethod.PICKUP,
                )
                .order_by(Order.updated_at)
            )
        )

    def list_active_for_courier(self, courier_id: int) -> list[Order]:
        """Orders the courier has taken and not delivered yet."""
        return list(
            self._session.scalars(
                self._with_courier_details()
                .where(
                    Order.courier_id == courier_id,
                    Order.status.in_([OrderStatus.READY_FOR_PICKUP, OrderStatus.DELIVERING]),
                )
                .order_by(Order.created_at)
            )
        )

    def page_for_customer(self, customer_id: int, page: int, per_page: int) -> PageResult[Order]:
        """The customer's orders, newest first."""
        total = (
            self._session.scalar(
                select(func.count(Order.id)).where(Order.customer_id == customer_id)
            )
            or 0
        )
        items = list(
            self._session.scalars(
                select(Order)
                .where(Order.customer_id == customer_id)
                .options(selectinload(Order.items), selectinload(Order.restaurant))
                .order_by(Order.created_at.desc(), Order.id.desc())
                .offset((page - 1) * per_page)
                .limit(per_page)
            )
        )
        return PageResult(items=items, total=total, page=page, per_page=per_page)

    def past_order(self, order_id: int, customer_id: int) -> PastOrder | None:
        """Implements `PastOrders` for `ReorderCommand`: the order as plain data."""
        order = self.get_with_details(order_id)
        if order is None or order.customer_id != customer_id:
            return None
        return PastOrder(
            restaurant_id=order.restaurant.id,
            restaurant_name=order.restaurant.name,
            restaurant_active=order.restaurant.is_active,
            restaurant_min_order=order.restaurant.min_order_amount,
            items=[
                PastOrderItem(item.dish_id, item.name, item.price, item.quantity)
                for item in order.items
            ],
        )
