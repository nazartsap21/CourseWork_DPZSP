from flask import Blueprint, Response, jsonify

from ...container import get_services
from ...models import UserRole
from ...schemas.loyalty import (
    BonusTransactionOut,
    LoyaltyOut,
    LoyaltyRulesOut,
    PaymentRedirectOut,
    PremiumPurchaseIn,
)
from ..security import current_user_id, roles_required
from ..validation import parse_body

loyalty_bp = Blueprint("loyalty", __name__, url_prefix="/loyalty")


@loyalty_bp.get("")
@roles_required(UserRole.CUSTOMER)
def my_loyalty() -> Response:
    summary = get_services().loyalty.summary(current_user_id())
    account, status, rules = summary.account, summary.status, summary.rules
    out = LoyaltyOut(
        points_balance=account.points_balance,
        card_type=account.card_type,
        premium_until=account.premium_until,
        has_premium=status.has_premium,
        completed_orders=account.completed_orders_count,
        is_regular=status.is_regular,
        orders_to_regular=max(rules.regular_customer_threshold - account.completed_orders_count, 0),
        rules=LoyaltyRulesOut(
            **vars(rules),
            premium_card_price=summary.premium_price,
            premium_card_days=summary.premium_days,
        ),
        transactions=[BonusTransactionOut.model_validate(t) for t in summary.transactions],
    )
    return jsonify(out.model_dump(mode="json"))


@loyalty_bp.post("/premium")
@roles_required(UserRole.CUSTOMER)
def buy_premium() -> tuple[Response, int]:
    """Starts paying for the premium card through the regular payment flow;
    the card is activated when `/payments/confirm` verifies the payment."""
    body = parse_body(PremiumPurchaseIn)
    redirect_url = get_services().loyalty.buy_premium(current_user_id(), body.payment_method)
    return jsonify(PaymentRedirectOut(redirect_url=redirect_url).model_dump()), 201
