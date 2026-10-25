from dataclasses import dataclass
from datetime import datetime

KOPIYKY_PER_100_UAH = 10_000


@dataclass(frozen=True)
class LoyaltyRules:
    """Plain copy of the LoyaltySettings row, so pricing doesn't depend on the ORM.
    Money values are kopiyky; percentages are whole numbers."""

    points_per_100_uah: int
    point_value: int
    max_points_redemption_percent: int
    regular_customer_threshold: int
    regular_customer_discount_percent: int


@dataclass(frozen=True)
class LoyaltyStatus:
    is_regular: bool
    has_premium: bool
    points_balance: int


GUEST_LOYALTY = LoyaltyStatus(is_regular=False, has_premium=False, points_balance=0)


def loyalty_status(
    rules: LoyaltyRules,
    completed_orders: int,
    card_type: str,
    premium_until: datetime | None,
    points_balance: int,
    now: datetime,
) -> LoyaltyStatus:
    return LoyaltyStatus(
        is_regular=completed_orders >= rules.regular_customer_threshold,
        has_premium=card_type == "premium" and premium_until is not None and premium_until > now,
        points_balance=points_balance,
    )


def points_earned(rules: LoyaltyRules, paid_total: int) -> int:
    """Points for a delivered order: `points_per_100_uah` for every full 100 UAH paid."""
    return paid_total // KOPIYKY_PER_100_UAH * rules.points_per_100_uah


def max_redeemable_points(rules: LoyaltyRules, subtotal: int, points_balance: int) -> int:
    """Points can cover at most `max_points_redemption_percent` of the dishes subtotal."""
    cap_amount = subtotal * rules.max_points_redemption_percent // 100
    return min(points_balance, cap_amount // rules.point_value) if rules.point_value else 0
