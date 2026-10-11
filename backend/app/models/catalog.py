from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db
from .base import utcnow

if TYPE_CHECKING:
    from .account import Review

restaurant_cuisines = Table(
    "restaurant_cuisines",
    db.metadata,
    Column("restaurant_id", ForeignKey("restaurants.id", ondelete="CASCADE"), primary_key=True),
    Column("cuisine_id", ForeignKey("cuisines.id", ondelete="CASCADE"), primary_key=True),
)


class Cuisine(db.Model):
    __tablename__ = "cuisines"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)

    restaurants: Mapped[list[Restaurant]] = relationship(
        secondary=restaurant_cuisines, back_populates="cuisines"
    )


class Restaurant(db.Model):
    """Money columns (min_order_amount) are integer kopiyky."""

    __tablename__ = "restaurants"
    __table_args__ = (
        CheckConstraint("avg_prep_minutes > 0", name="avg_prep_minutes_positive"),
        CheckConstraint("min_order_amount >= 0", name="min_order_amount_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    address: Mapped[str] = mapped_column(String(255))
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    avg_prep_minutes: Mapped[int] = mapped_column(Integer, default=20)
    min_order_amount: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    image_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    cuisines: Mapped[list[Cuisine]] = relationship(
        secondary=restaurant_cuisines, back_populates="restaurants"
    )
    dishes: Mapped[list[Dish]] = relationship(
        back_populates="restaurant", cascade="all, delete-orphan", order_by="Dish.id"
    )
    reviews: Mapped[list[Review]] = relationship(back_populates="restaurant")


class Dish(db.Model):
    """`price` is integer kopiyky."""

    __tablename__ = "dishes"
    __table_args__ = (
        UniqueConstraint("restaurant_id", "name", name="uq_dishes_restaurant_id_name"),
        CheckConstraint("price >= 0", name="price_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey("restaurants.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    price: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(64))
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    image_url: Mapped[str | None] = mapped_column(String(500))

    restaurant: Mapped[Restaurant] = relationship(back_populates="dishes")
