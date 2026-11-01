from datetime import UTC, datetime, time

from sqlalchemy import func, select
from sqlalchemy.orm import aliased

from ..domain.reports.base import ReportPeriod
from ..domain.reports.reports import DeliveryRecord, OrderRecord, SoldItemRecord
from ..models import Order, OrderItem, OrderStatus, OrderStatusHistory, Restaurant, User
from .base import SqlAlchemyRepository


def _created_in(period: ReportPeriod) -> tuple:
    """Inclusive calendar days, interpreted in UTC, as a [start, end) range."""
    start = datetime.combine(period.start, time.min, UTC)
    end = datetime.combine(period.end_exclusive, time.min, UTC)
    return Order.created_at >= start, Order.created_at < end


class ReportRepository(SqlAlchemyRepository):
    """Implements `ReportDataSource`: flat rows for the report generators.
    Grouping happens in the reports themselves, so the queries stay simple."""

    def orders_created(self, period: ReportPeriod) -> list[OrderRecord]:
        rows = self._session.execute(
            select(Restaurant.name, Order.status, Order.discount, Order.total)
            .join(Restaurant, Order.restaurant_id == Restaurant.id)
            .where(*_created_in(period))
        ).all()
        return [
            OrderRecord(name, status.value, discount, total)
            for name, status, discount, total in rows
        ]

    def items_delivered(self, period: ReportPeriod) -> list[SoldItemRecord]:
        rows = self._session.execute(
            select(Restaurant.name, OrderItem.name, OrderItem.quantity, OrderItem.price, Order.id)
            .join(Order, OrderItem.order_id == Order.id)
            .join(Restaurant, Order.restaurant_id == Restaurant.id)
            .where(Order.status == OrderStatus.DELIVERED, *_created_in(period))
        ).all()
        return [
            SoldItemRecord(restaurant, dish, quantity, price * quantity, order_id)
            for restaurant, dish, quantity, price, order_id in rows
        ]

    def courier_deliveries(self, period: ReportPeriod) -> list[DeliveryRecord]:
        courier = aliased(User)
        # When the order reached "delivered", from the status history.
        delivered_at = (
            select(func.max(OrderStatusHistory.changed_at))
            .where(
                OrderStatusHistory.order_id == Order.id,
                OrderStatusHistory.status == OrderStatus.DELIVERED,
            )
            .correlate(Order)
            .scalar_subquery()
        )
        rows = self._session.execute(
            select(
                courier.name,
                Order.total,
                Order.created_at,
                Order.picked_up_at,
                delivered_at,
                Order.estimated_delivery_minutes,
            )
            .join(courier, Order.courier_id == courier.id)
            .where(Order.status == OrderStatus.DELIVERED, *_created_in(period))
        ).all()
        return [DeliveryRecord(*row) for row in rows]
