from .decorators import (
    BaseOrderPrice,
    BonusPointsRedemption,
    PremiumFreeDelivery,
    PriceBreakdown,
    PriceComponent,
    RegularCustomerDiscount,
)
from .loyalty import LoyaltyRules, LoyaltyStatus


def build_order_price(
    subtotal: int,
    delivery_fee: int,
    status: LoyaltyStatus,
    rules: LoyaltyRules,
    requested_points: int = 0,
) -> PriceComponent:
    """Decides which decorators apply to this customer and in which order.

    Percentage discount first (on dishes), then free delivery, then points last,
    so the points cap is checked against what the customer would actually pay.
    """
    price: PriceComponent = BaseOrderPrice(subtotal, delivery_fee)
    if status.is_regular and rules.regular_customer_discount_percent > 0:
        price = RegularCustomerDiscount(price, rules.regular_customer_discount_percent)
    if status.has_premium and delivery_fee > 0:
        price = PremiumFreeDelivery(price)
    points = min(requested_points, status.points_balance)
    if points > 0:
        price = BonusPointsRedemption(
            price, points, rules.point_value, rules.max_points_redemption_percent
        )
    return price


def calculate_order_price(
    subtotal: int,
    delivery_fee: int,
    status: LoyaltyStatus,
    rules: LoyaltyRules,
    requested_points: int = 0,
) -> PriceBreakdown:
    return PriceBreakdown.from_component(
        build_order_price(subtotal, delivery_fee, status, rules, requested_points)
    )
