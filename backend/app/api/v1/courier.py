from flask import Blueprint, Response, jsonify

from ...container import get_services
from ...domain.orders.permissions import Actor
from ...models import Order, OrderStatus, UserRole
from ...schemas.orders import CourierOrderOut, CustomerContactOut
from ..security import current_user_id, roles_required

courier_bp = Blueprint("courier", __name__, url_prefix="/courier")


def _card(order: Order, actor: Actor) -> dict:
    card = CourierOrderOut.model_validate(order)
    # Contact details only once the order is this courier's job.
    if order.courier_id == actor.user_id:
        card.customer = CustomerContactOut.model_validate(order.customer)
    card.available_transitions = [
        OrderStatus(status) for status in get_services().orders.available_transitions(order, actor)
    ]
    return card.model_dump(mode="json")


def _actor() -> Actor:
    return Actor(user_id=current_user_id(), role=UserRole.COURIER)


@courier_bp.get("/orders/available")
@roles_required(UserRole.COURIER)
def available_orders() -> Response:
    actor = _actor()
    return jsonify({"items": [_card(o, actor) for o in get_services().courier.available()]})


@courier_bp.get("/orders/active")
@roles_required(UserRole.COURIER)
def active_orders() -> Response:
    actor = _actor()
    orders = get_services().courier.active(actor.user_id)
    return jsonify({"items": [_card(o, actor) for o in orders]})


@courier_bp.post("/orders/<int:order_id>/take")
@roles_required(UserRole.COURIER)
def take_order(order_id: int) -> Response:
    actor = _actor()
    return jsonify(_card(get_services().courier.take(order_id, actor.user_id), actor))
