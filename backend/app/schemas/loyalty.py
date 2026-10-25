from datetime import datetime

from pydantic import BaseModel, ConfigDict

from ..models import BonusReason, CardType, PaymentMethod


class BonusTransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    delta: int
    reason: BonusReason
    order_id: int | None
    created_at: datetime


class LoyaltyRulesOut(BaseModel):
    """Money values in kopiyky; percentages are whole numbers."""

    points_per_100_uah: int
    point_value: int
    max_points_redemption_percent: int
    regular_customer_threshold: int
    regular_customer_discount_percent: int
    premium_card_price: int
    premium_card_days: int


class LoyaltyOut(BaseModel):
    points_balance: int
    card_type: CardType
    premium_until: datetime | None
    has_premium: bool
    completed_orders: int
    is_regular: bool
    # Orders still needed for the regular-customer discount (0 once reached).
    orders_to_regular: int
    rules: LoyaltyRulesOut
    transactions: list[BonusTransactionOut]


class PremiumPurchaseIn(BaseModel):
    payment_method: PaymentMethod = PaymentMethod.STRIPE


class PaymentRedirectOut(BaseModel):
    redirect_url: str
