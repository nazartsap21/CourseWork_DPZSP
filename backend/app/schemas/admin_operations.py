"""Admin operations payloads. Money fields are integer kopiyky; percentages are whole numbers."""

from datetime import date, datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from ..models import DeliveryMethod, OrderStatus, PaymentMethod, PaymentStatus
from .auth import Email, Name, Phone
from .common import PageParams


class CourierIn(BaseModel):
    name: Name
    email: Email
    phone: Phone = None
    password: str = Field(min_length=8, max_length=128)


class CourierOut(BaseModel):
    id: int
    name: str
    email: str
    phone: str | None
    active_order_ids: list[int]
    delivered_today: int


class AdminOrderListParams(PageParams):
    status: OrderStatus | None = None
    restaurant_id: int | None = Field(default=None, ge=1)
    date_from: date | None = None
    date_to: date | None = None

    @model_validator(mode="after")
    def dates_in_order(self) -> Self:
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("The start date must not be after the end date.")
        return self


class AdminOrderRowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: OrderStatus
    delivery_method: DeliveryMethod
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    total: int
    created_at: datetime
    restaurant_name: str
    customer_name: str
    courier_name: str | None


class LoyaltySettingsIO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    points_per_100_uah: int = Field(ge=0, le=100)
    point_value: int = Field(ge=1, le=10_000)
    max_points_redemption_percent: int = Field(ge=0, le=100)
    regular_customer_threshold: int = Field(ge=1, le=1000)
    regular_customer_discount_percent: int = Field(ge=0, le=50)
    premium_card_price: int = Field(ge=100, le=100_000)
    premium_card_days: int = Field(ge=1, le=365)


class PromotionIn(BaseModel):
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=500)]


class PromotionOut(BaseModel):
    recipients: int
