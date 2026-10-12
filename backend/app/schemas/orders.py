from typing import Self

from pydantic import BaseModel, Field, model_validator

from ..models import DeliveryMethod

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
    # First broken order rule (minimum order, zone, ...); null when the order can be placed.
    validation_error: ValidationIssueOut | None
