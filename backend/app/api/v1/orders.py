from dataclasses import replace

from flask import Blueprint, Response, jsonify
from flask_jwt_extended import get_jwt, jwt_required

from ...container import get_services
from ...domain.delivery.geo import GeoPoint
from ...models import Order, UserRole
from ...schemas.orders import (
    CheckoutIn,
    DeliveryOut,
    LoyaltyOut,
    OrderOut,
    PriceLineOut,
    QuotedItemOut,
    QuoteIn,
    QuoteOut,
    ValidationIssueOut,
)
from ...services.checkout_facade import CheckoutRequest
from ...services.quote_service import Quote, QuoteItemRequest, QuoteRequest
from ..security import current_user_id, roles_required
from ..validation import parse_body

orders_bp = Blueprint("orders", __name__, url_prefix="/orders")


def _quote_out(quote: Quote) -> QuoteOut:
    price = quote.price
    error = quote.validation_error
    return QuoteOut(
        restaurant_id=quote.draft.restaurant.id,
        items=[
            QuotedItemOut(
                dish_id=item.dish.id,
                name=item.dish.name,
                price=item.dish.price,
                quantity=item.quantity,
                line_total=item.line_total,
                is_available=item.dish.is_available,
            )
            for item in quote.draft.items
        ],
        delivery=DeliveryOut(
            method=quote.delivery.method,
            fee=quote.delivery.fee,
            eta_minutes_min=quote.delivery.eta_minutes_min,
            eta_minutes_max=quote.delivery.eta_minutes_max,
            distance_km=round(quote.delivery.distance_km, 2)
            if quote.delivery.distance_km is not None
            else None,
            needs_courier=quote.delivery.needs_courier,
            is_priority=quote.delivery.is_priority,
        ),
        lines=[PriceLineOut(code=ln.code, label=ln.label, amount=ln.amount) for ln in price.lines],
        subtotal=price.subtotal,
        delivery_fee=price.delivery_fee,
        discount=price.discount,
        bonus_points_used=price.bonus_points_used,
        total=price.total,
        loyalty=LoyaltyOut(
            is_regular=quote.loyalty.is_regular,
            has_premium=quote.loyalty.has_premium,
            points_balance=quote.loyalty.points_balance,
            max_redeemable_points=quote.max_redeemable_points,
        ),
        validation_error=ValidationIssueOut(
            code=error.code, message=error.message, field=error.field
        )
        if error
        else None,
    )


def _quote_request(body: QuoteIn) -> QuoteRequest:
    destination = (
        GeoPoint(body.delivery_lat, body.delivery_lng)
        if body.delivery_lat is not None and body.delivery_lng is not None
        else None
    )
    return QuoteRequest(
        restaurant_id=body.restaurant_id,
        items=[QuoteItemRequest(i.dish_id, i.quantity) for i in body.items],
        delivery_method=body.delivery_method,
        destination=destination,
        bonus_points=body.bonus_points,
    )


def _order_out(order: Order) -> dict:
    return OrderOut.model_validate(order).model_dump(mode="json")


@orders_bp.post("/quote")
@jwt_required(optional=True)
def quote() -> Response:
    """Price breakdown for a cart. Guests get base prices; signed-in customers
    also get their loyalty discounts. Broken order rules come back as
    `validation_error` (status 200) so the checkout can show them next to the price."""
    body = parse_body(QuoteIn)
    is_customer = get_jwt().get("role") == UserRole.CUSTOMER
    result = get_services().quotes.quote(
        _quote_request(body), customer_id=current_user_id() if is_customer else None
    )
    return jsonify(_quote_out(result).model_dump(mode="json"))


@orders_bp.post("")
@roles_required(UserRole.CUSTOMER)
def place_order() -> tuple[Response, int]:
    """Places an order through the CheckoutFacade. Broken order rules → 422."""
    body = parse_body(CheckoutIn)
    request = replace(
        _quote_request(body),
        delivery_address=body.delivery_address,
        delivery_note=body.delivery_note,
    )
    order = get_services().checkout.place_order(
        CheckoutRequest(quote=request, payment_method=body.payment_method),
        customer_id=current_user_id(),
    )
    return jsonify(_order_out(order)), 201


@orders_bp.get("/<int:order_id>")
@jwt_required()
def get_order(order_id: int) -> Response:
    order = get_services().orders.get_order(order_id, current_user_id(), get_jwt()["role"])
    return jsonify(_order_out(order))
