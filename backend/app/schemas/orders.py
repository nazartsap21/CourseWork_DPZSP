from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

from ..models import DeliveryMethod, OrderStatus, PaymentMethod, PaymentStatus

MAX_ITEM_QUANTITY = 20
MAX_DISTINCT_ITEMS = 50


class OrderItemIn(BaseModel):
    """Only id and quantity: the price is always taken from the database."""

    dish_id: int = Field(ge=1)
    quantity: int = Field(ge=1, le=MAX_ITEM_QUANTITY)


class QuoteIn(BaseModel):
    restaurant_id: int = Field(ge=1)
    items: list[OrderItemIn] = Field(min_length=1, max_length=MAX_DISTINCT_ITEMS)
    delivery_method: DeliveryMethod
    delivery_lat: float | None = Field(default=None, ge=-90, le=90)
    delivery_lng: float | None = Field(default=None, ge=-180, le=180)
    bonus_points: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def coordinates_come_in_pairs(self) -> Self:
        if (self.delivery_lat is None) != (self.delivery_lng is None):
            raise ValueError("Send both delivery_lat and delivery_lng, or neither.")
        return self


class QuotedItemOut(BaseModel):
    """Money fields are integer kopiyky."""

    dish_id: int
    name: str
    price: int
    quantity: int
    line_total: int
    is_available: bool


class PriceLineOut(BaseModel):
    code: str
    label: str
    amount: int


class DeliveryOut(BaseModel):
    method: DeliveryMethod
    fee: int
    eta_minutes_min: int
    eta_minutes_max: int
    distance_km: float | None
    needs_courier: bool
    is_priority: bool


class LoyaltyOut(BaseModel):
    is_regular: bool
    has_premium: bool
    points_balance: int
    max_redeemable_points: int


class ValidationIssueOut(BaseModel):
    code: str
    message: str
    field: str | None


class QuoteOut(BaseModel):
    """`lines` explain the total in display order; the flat fields match the Order columns."""

    restaurant_id: int
    items: list[QuotedItemOut]
    delivery: DeliveryOut
    lines: list[PriceLineOut]
    subtotal: int
    delivery_fee: int
    discount: int
    bonus_points_used: int
    total: int
    loyalty: LoyaltyOut
    # Courier delivery zone around the restaurant, for drawing it on the map.
    delivery_radius_km: float
    # First broken order rule (minimum order, zone, ...); null when the order can be placed.
    validation_error: ValidationIssueOut | None


class CheckoutIn(QuoteIn):
    payment_method: PaymentMethod
    # Validated even when omitted, so a missing address is reported on this field.
    delivery_address: str | None = Field(default=None, max_length=255, validate_default=True)
    delivery_note: str | None = Field(default=None, max_length=255)

    @field_validator("delivery_note")
    @classmethod
    def blank_note_is_none(cls, value: str | None) -> str | None:
        return (value or "").strip() or None

    @field_validator("delivery_address")
    @classmethod
    def courier_needs_address(cls, value: str | None, info: ValidationInfo) -> str | None:
        value = (value or "").strip() or None
        if value is None and info.data.get("delivery_method") not in (None, DeliveryMethod.PICKUP):
            raise ValueError("Enter the street and building for the courier.")
        return value


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dish_id: int | None
    name: str
    price: int
    quantity: int


class StatusChangeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: OrderStatus
    changed_at: datetime


class OrderRestaurantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    address: str
    lat: float
    lng: float


class OrderOut(BaseModel):
    """Money fields are integer kopiyky."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: OrderStatus
    restaurant: OrderRestaurantOut
    items: list[OrderItemOut]
    delivery_method: DeliveryMethod
    delivery_address: str | None
    delivery_note: str | None
    delivery_lat: float | None
    delivery_lng: float | None
    subtotal: int
    delivery_fee: int
    discount: int
    bonus_points_used: int
    total: int
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    estimated_delivery_minutes: int | None
    created_at: datetime
    status_history: list[StatusChangeOut]
    # Statuses the current viewer may move the order to (buttons in staff UIs).
    available_transitions: list[OrderStatus] = []


class StatusChangeIn(BaseModel):
    status: OrderStatus


class PlacedOrderOut(OrderOut):
    # Send the customer here to pay (Stripe or the mock success page); null for cash.
    payment_redirect_url: str | None


class PaymentConfirmIn(BaseModel):
    session_id: str = Field(min_length=1, max_length=255)


class PaymentSessionOut(BaseModel):
    redirect_url: str
