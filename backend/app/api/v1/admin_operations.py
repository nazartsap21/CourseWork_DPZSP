from flask import Blueprint, Response, jsonify

from ...container import get_services
from ...models import UserRole
from ...schemas.admin_operations import (
    AdminOrderListParams,
    AdminOrderRowOut,
    CourierIn,
    CourierOut,
    LoyaltySettingsIO,
    PromotionIn,
    PromotionOut,
)
from ...schemas.common import Page
from ...services.admin_operations_service import OrderFilters
from ..security import roles_required
from ..validation import parse_body, parse_query

# Same URL space as the catalog admin; order details, status changes and cancel
# use the shared /orders endpoints, where admins already have full access.
admin_operations_bp = Blueprint("admin_operations", __name__, url_prefix="/admin")


@admin_operations_bp.before_request
@roles_required(UserRole.ADMIN)
def require_admin() -> None:
    """Every route in this blueprint is admin-only."""


@admin_operations_bp.get("/couriers")
def list_couriers() -> Response:
    items = [
        CourierOut(
            id=s.courier.id,
            name=s.courier.name,
            email=s.courier.email,
            phone=s.courier.phone,
            active_order_ids=s.active_order_ids,
            delivered_today=s.delivered_today,
        )
        for s in get_services().admin_operations.couriers()
    ]
    return jsonify({"items": [item.model_dump() for item in items]})


@admin_operations_bp.post("/couriers")
def create_courier() -> tuple[Response, int]:
    body = parse_body(CourierIn)
    courier = get_services().admin_operations.create_courier(
        body.name, body.email, body.phone, body.password
    )
    out = CourierOut(
        id=courier.id,
        name=courier.name,
        email=courier.email,
        phone=courier.phone,
        active_order_ids=[],
        delivered_today=0,
    )
    return jsonify(out.model_dump()), 201


@admin_operations_bp.get("/orders")
def list_orders() -> Response:
    params = parse_query(AdminOrderListParams)
    result = get_services().admin_operations.orders(
        OrderFilters(params.status, params.restaurant_id, params.date_from, params.date_to),
        params.page,
        params.per_page,
    )
    page = Page[AdminOrderRowOut](
        items=[
            AdminOrderRowOut(
                id=o.id,
                status=o.status,
                delivery_method=o.delivery_method,
                payment_method=o.payment_method,
                payment_status=o.payment_status,
                total=o.total,
                created_at=o.created_at,
                restaurant_name=o.restaurant.name,
                customer_name=o.customer.name,
                courier_name=o.courier.name if o.courier else None,
            )
            for o in result.items
        ],
        total=result.total,
        page=result.page,
        per_page=result.per_page,
        pages=result.pages,
    )
    return jsonify(page.model_dump(mode="json"))


@admin_operations_bp.get("/loyalty-settings")
def get_loyalty_settings() -> Response:
    settings = get_services().admin_operations.loyalty_settings()
    return jsonify(LoyaltySettingsIO.model_validate(settings).model_dump())


@admin_operations_bp.put("/loyalty-settings")
def update_loyalty_settings() -> Response:
    values = parse_body(LoyaltySettingsIO).model_dump()
    settings = get_services().admin_operations.update_loyalty_settings(values)
    return jsonify(LoyaltySettingsIO.model_validate(settings).model_dump())


@admin_operations_bp.post("/promotions")
def send_promotion() -> tuple[Response, int]:
    body = parse_body(PromotionIn)
    recipients = get_services().admin_operations.send_promotion(body.message)
    return jsonify(PromotionOut(recipients=recipients).model_dump()), 201
