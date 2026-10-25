from dataclasses import replace

from flask import Blueprint, Response, jsonify
from flask_jwt_extended import get_jwt, jwt_required

from ...container import get_services
from ...domain.delivery.geo import GeoPoint
from ...domain.orders.permissions import Actor
from ...models import Order, OrderStatus, UserRole
from ...schemas.common import Page, PageParams
from ...schemas.orders import (
    CheckoutIn,
    DeliveryOut,
    LoyaltyOut,
    OrderOut,
    OrderSummaryOut,
    PaymentSessionOut,
    PlacedOrderOut,
    PriceLineOut,
    QuotedItemOut,
    QuoteIn,
    QuoteOut,
    StatusChangeIn,
    TrackingOut,
    ValidationIssueOut,
)
from ...services.checkout_facade import CheckoutRequest
from ...services.quote_service import Quote, QuoteItemRequest, QuoteRequest
from ..security import current_user_id, roles_required
from ..validation import parse_body, parse_query

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
        delivery_radius_km=quote.delivery_radius_km,
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
    """Places an order through the CheckoutFacade. Broken order rules → 422.
    For online payment the response carries `payment_redirect_url`."""
    body = parse_body(CheckoutIn)
    request = replace(
        _quote_request(body),
        delivery_address=body.delivery_address,
        delivery_note=body.delivery_note,
    )
    result = get_services().checkout.place_order(
        CheckoutRequest(quote=request, payment_method=body.payment_method),
        customer_id=current_user_id(),
    )
    placed = PlacedOrderOut.model_validate(
        {
            **OrderOut.model_validate(result.order).model_dump(),
            "payment_redirect_url": result.payment_redirect_url,
        }
    )
    return jsonify(placed.model_dump(mode="json")), 201


def _current_actor() -> Actor:
    return Actor(user_id=current_user_id(), role=get_jwt()["role"])


def _order_detail(order: Order, actor: Actor) -> dict:
    detail = OrderOut.model_validate(order)
    detail.available_transitions = [
        OrderStatus(status) for status in get_services().orders.available_transitions(order, actor)
    ]
    return detail.model_dump(mode="json")


@orders_bp.get("/<int:order_id>")
@jwt_required()
def get_order(order_id: int) -> Response:
    actor = _current_actor()
    return jsonify(_order_detail(get_services().orders.get_order(order_id, actor), actor))


@orders_bp.patch("/<int:order_id>/status")
@roles_required(UserRole.ADMIN, UserRole.COURIER)
def change_status(order_id: int) -> Response:
    """Staff move an order along its lifecycle: the OrderState rejects impossible
    moves (409), the permission policy rejects the wrong person (403)."""
    body = parse_body(StatusChangeIn)
    actor = _current_actor()
    order = get_services().orders.change_status(order_id, body.status, actor)
    return jsonify(_order_detail(order, actor))


@orders_bp.post("/<int:order_id>/payment-session")
@roles_required(UserRole.CUSTOMER)
def restart_payment(order_id: int) -> tuple[Response, int]:
    """Another payment attempt for an order still waiting for payment."""
    redirect_url = get_services().payments.restart(order_id, current_user_id())
    return jsonify(PaymentSessionOut(redirect_url=redirect_url).model_dump()), 201


@orders_bp.get("/<int:order_id>/tracking")
@jwt_required()
def tracking(order_id: int) -> Response:
    """Route and the simulated courier position; the tracking page polls this."""
    result = get_services().orders.tracking(order_id, _current_actor())
    order, courier = result.order, result.courier
    out = TrackingOut(
        order_id=order.id,
        status=order.status,
        delivery_method=order.delivery_method,
        restaurant={"lat": order.restaurant.lat, "lng": order.restaurant.lng},
        destination={"lat": order.delivery_lat, "lng": order.delivery_lng}
        if order.delivery_lat is not None and order.delivery_lng is not None
        else None,
        route=[(p.lat, p.lng) for p in result.route],
        courier={
            "lat": courier.point.lat,
            "lng": courier.point.lng,
            "progress": round(courier.progress, 3),
            "minutes_left": courier.minutes_left,
        }
        if courier
        else None,
    )
    return jsonify(out.model_dump(mode="json"))


@orders_bp.get("")
@roles_required(UserRole.CUSTOMER)
def order_history() -> Response:
    """The signed-in customer's orders, newest first (`?page=&per_page=`)."""
    params = parse_query(PageParams)
    result = get_services().orders.history(current_user_id(), params.page, params.per_page)
    page = Page[OrderSummaryOut](
        items=[OrderSummaryOut.model_validate(order) for order in result.items],
        total=result.total,
        page=result.page,
        per_page=result.per_page,
        pages=result.pages,
    )
    return jsonify(page.model_dump(mode="json"))
