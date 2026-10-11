from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, CheckConstraint, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db
from .base import enum_column, utcnow
from .enums import DeliveryMethod, OrderStatus, PaymentMethod, PaymentStatus

if TYPE_CHECKING:
    from .account import Review
    from .catalog import Dish, Restaurant
    from .payment import Payment
    from .user import User


class Order(db.Model):
    """All money columns are integer kopiyky; `bonus_points_used` is a point count.

    `status` holds the persisted name of the current `OrderState`; the State
    pattern objects (domain/orders/states.py) are rebuilt from it on load.
    """

    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="subtotal_non_negative"),
        CheckConstraint("delivery_fee >= 0", name="delivery_fee_non_negative"),
        CheckConstraint("discount >= 0", name="discount_non_negative"),
        CheckConstraint("bonus_points_used >= 0", name="bonus_points_used_non_negative"),
        CheckConstraint("total >= 0", name="total_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), index=True)
    courier_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    status: Mapped[OrderStatus] = mapped_column(
        enum_column(OrderStatus), default=OrderStatus.PENDING_PAYMENT, index=True
    )
    delivery_method: Mapped[DeliveryMethod] = mapped_column(enum_column(DeliveryMethod))
    # Delivery point is empty for pickup orders.
    delivery_address: Mapped[str | None] = mapped_column(String(255))
    delivery_note: Mapped[str | None] = mapped_column(String(255))
    delivery_lat: Mapped[float | None] = mapped_column(Float)
    delivery_lng: Mapped[float | None] = mapped_column(Float)

    subtotal: Mapped[int] = mapped_column(Integer, default=0)
    delivery_fee: Mapped[int] = mapped_column(Integer, default=0)
    discount: Mapped[int] = mapped_column(Integer, default=0)
    bonus_points_used: Mapped[int] = mapped_column(Integer, default=0)
    total: Mapped[int] = mapped_column(Integer, default=0)

    payment_method: Mapped[PaymentMethod] = mapped_column(enum_column(PaymentMethod))
    payment_status: Mapped[PaymentStatus] = mapped_column(
        enum_column(PaymentStatus), default=PaymentStatus.PENDING
    )

    # Courier route as a list of [lat, lng] points, stored when the order is picked up.
    route: Mapped[list[list[float]] | None] = mapped_column(JSON)
    picked_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    estimated_delivery_minutes: Mapped[int | None] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    customer: Mapped[User] = relationship(back_populates="orders", foreign_keys=[customer_id])
    courier: Mapped[User | None] = relationship(foreign_keys=[courier_id])
    restaurant: Mapped[Restaurant] = relationship()
    items: Mapped[list[OrderItem]] = relationship(
        back_populates="order", cascade="all, delete-orphan", order_by="OrderItem.id"
    )
    status_history: Mapped[list[OrderStatusHistory]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderStatusHistory.changed_at",
    )
    payments: Mapped[list[Payment]] = relationship(back_populates="order")
    review: Mapped[Review | None] = relationship(back_populates="order")


class OrderItem(db.Model):
    """Name and price are snapshots so history stays correct after menu edits."""

    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("price >= 0", name="price_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    dish_id: Mapped[int | None] = mapped_column(ForeignKey("dishes.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(120))
    price: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer)

    order: Mapped[Order] = relationship(back_populates="items")
    dish: Mapped[Dish | None] = relationship()


class OrderStatusHistory(db.Model):
    __tablename__ = "order_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    status: Mapped[OrderStatus] = mapped_column(enum_column(OrderStatus))
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    # Null when the change was made by the system (e.g. payment confirmation).
    changed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    order: Mapped[Order] = relationship(back_populates="status_history")
    changed_by: Mapped[User | None] = relationship()
