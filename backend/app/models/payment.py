from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db
from .base import enum_column, utcnow
from .enums import PaymentMethod, PaymentPurpose, PaymentStatus

if TYPE_CHECKING:
    from .order import Order
    from .user import User


class Payment(db.Model):
    """A payment attempt through one gateway. `amount` is integer kopiyky.

    The premium loyalty card is bought through the same payment flow as an
    order, so `order_id` is nullable and `purpose` tells the two apart.
    """

    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="amount_non_negative"),
        CheckConstraint(
            "(purpose = 'order' AND order_id IS NOT NULL) OR purpose <> 'order'",
            name="order_payment_has_order",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    order_id: Mapped[int | None] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )
    purpose: Mapped[PaymentPurpose] = mapped_column(
        enum_column(PaymentPurpose), default=PaymentPurpose.ORDER
    )
    provider: Mapped[PaymentMethod] = mapped_column(enum_column(PaymentMethod))
    # Stripe Checkout Session id; empty for cash and mock payments.
    external_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    amount: Mapped[int] = mapped_column(Integer)
    status: Mapped[PaymentStatus] = mapped_column(
        enum_column(PaymentStatus), default=PaymentStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    customer: Mapped[User] = relationship()
    order: Mapped[Order | None] = relationship(back_populates="payments")
