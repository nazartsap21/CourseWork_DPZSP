"""Who may move an order, kept apart from the State classes.

States answer "is this move possible from here?"; this module answers "may
this person make it?". Keeping them separate means a new role or a staff
rule changes here only, and the lifecycle diagram stays the same (SRP).
"""

from dataclasses import dataclass

from ..errors import PermissionDeniedError

ADMIN = "admin"
COURIER = "courier"
CUSTOMER = "customer"


@dataclass(frozen=True)
class Actor:
    user_id: int
    role: str


@dataclass(frozen=True)
class OrderAccess:
    customer_id: int
    courier_id: int | None
    is_pickup: bool


def is_allowed(action: str, actor: Actor, order: OrderAccess) -> bool:
    if action == "pay":
        # Only the payment flow confirms payments, never a person.
        return False
    if action in ("start_preparing", "mark_ready"):
        # The admin acts as restaurant staff.
        return actor.role == ADMIN
    if action == "pick_up":
        # A free courier may take an order; once taken, only that courier.
        return actor.role == COURIER and order.courier_id in (None, actor.user_id)
    if action == "deliver":
        if order.is_pickup:
            return actor.role == ADMIN
        return actor.role == COURIER and order.courier_id == actor.user_id
    if action == "cancel":
        return actor.role == ADMIN or (
            actor.role == CUSTOMER and order.customer_id == actor.user_id
        )
    return False


def authorize(action: str, actor: Actor, order: OrderAccess) -> None:
    if not is_allowed(action, actor, order):
        raise PermissionDeniedError(
            "You can't make this change to the order.", "STATUS_CHANGE_FORBIDDEN"
        )
