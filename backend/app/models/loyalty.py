from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db
from .base import enum_column, utcnow
from .enums import BonusReason, CardType

if TYPE_CHECKING:
    from .order import Order
    from .user import User


class LoyaltyAccount(db.Model):
    __tablename__ = "loyalty_accounts"
    __table_args__ = (CheckConstraint("points_balance >= 0", name="points_balance_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    points_balance: Mapped[int] = mapped_column(Integer, default=0)
    card_type: Mapped[CardType] = mapped_column(enum_column(CardType), default=CardType.STANDARD)
    premium_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_orders_count: Mapped[int] = mapped_column(Integer, default=0)

    customer: Mapped[User] = relationship(back_populates="loyalty_account")
    transactions: Mapped[list[BonusTransaction]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
        order_by="BonusTransaction.created_at.desc()",
    )


class BonusTransaction(db.Model):
    """Ledger of point changes; `delta` is positive for accrual, negative for spending."""

    __tablename__ = "bonus_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("loyalty_accounts.id", ondelete="CASCADE"), index=True
    )
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id", ondelete="SET NULL"))
    delta: Mapped[int] = mapped_column(Integer)
    reason: Mapped[BonusReason] = mapped_column(enum_column(BonusReason))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    account: Mapped[LoyaltyAccount] = relationship(back_populates="transactions")
    order: Mapped[Order | None] = relationship()


class LoyaltySettings(db.Model):
    """Single-row table (id = 1) edited from the admin panel.

    Money fields are integer kopiyky; percentages are whole numbers.
    """

    __tablename__ = "loyalty_settings"
    __table_args__ = (
        CheckConstraint("id = 1", name="single_row"),
        CheckConstraint(
            "regular_customer_discount_percent BETWEEN 0 AND 100",
            name="regular_discount_range",
        ),
        CheckConstraint(
            "max_points_redemption_percent BETWEEN 0 AND 100",
            name="max_redemption_range",
        ),
    )

    SINGLETON_ID = 1

    id: Mapped[int] = mapped_column(primary_key=True, default=SINGLETON_ID)
    points_per_100_uah: Mapped[int] = mapped_column(Integer, default=5)
    point_value: Mapped[int] = mapped_column(Integer, default=100)
    max_points_redemption_percent: Mapped[int] = mapped_column(Integer, default=30)
    regular_customer_threshold: Mapped[int] = mapped_column(Integer, default=5)
    regular_customer_discount_percent: Mapped[int] = mapped_column(Integer, default=5)
    premium_card_price: Mapped[int] = mapped_column(Integer, default=9900)
    premium_card_days: Mapped[int] = mapped_column(Integer, default=30)
