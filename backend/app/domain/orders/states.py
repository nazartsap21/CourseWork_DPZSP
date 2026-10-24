"""State pattern for the order lifecycle.

Each status is a class that decides which actions are allowed from it and
which state each action leads to. An action that isn't allowed raises
`InvalidTransitionError` (HTTP 409), so invalid moves like "deliver a
cancelled order" are impossible by construction, not by scattered `if`s.

States hold no per-order data, so one instance per status is shared
(see `state_for`). The persisted `Order.status` string is the link between
the database row and its state object.

Stage 9 implements what checkout needs: the initial state and the moves out
of it. The rest of the flow (preparing → delivered) is filled in with the
order status API.
"""

from abc import ABC

from ..errors import ConflictError


class InvalidTransitionError(ConflictError):
    code = "INVALID_STATUS_TRANSITION"


class OrderState(ABC):
    """Base state: every action is refused unless a subclass allows it."""

    status: str
    label: str

    def pay(self) -> "OrderState":
        raise self._refuse("confirm payment for")

    def start_preparing(self) -> "OrderState":
        raise self._refuse("start preparing")

    def mark_ready(self) -> "OrderState":
        raise self._refuse("mark as ready")

    def pick_up(self) -> "OrderState":
        raise self._refuse("hand to a courier")

    def deliver(self) -> "OrderState":
        raise self._refuse("mark as delivered")

    def cancel(self) -> "OrderState":
        raise self._refuse("cancel")

    @property
    def is_final(self) -> bool:
        return False

    def _refuse(self, action: str) -> InvalidTransitionError:
        return InvalidTransitionError(f"Can't {action} an order that is {self.label.lower()}.")


class PendingPayment(OrderState):
    status = "pending_payment"
    label = "Waiting for payment"

    def pay(self) -> OrderState:
        return ACCEPTED

    def cancel(self) -> OrderState:
        return CANCELLED


class Accepted(OrderState):
    status = "accepted"
    label = "Accepted"

    def cancel(self) -> OrderState:
        return CANCELLED


class Preparing(OrderState):
    status = "preparing"
    label = "Preparing"


class ReadyForPickup(OrderState):
    status = "ready_for_pickup"
    label = "Ready for pickup"


class Delivering(OrderState):
    status = "delivering"
    label = "On the way"


class Delivered(OrderState):
    status = "delivered"
    label = "Delivered"

    @property
    def is_final(self) -> bool:
        return True


class Cancelled(OrderState):
    status = "cancelled"
    label = "Cancelled"

    @property
    def is_final(self) -> bool:
        return True


PENDING_PAYMENT = PendingPayment()
ACCEPTED = Accepted()
PREPARING = Preparing()
READY_FOR_PICKUP = ReadyForPickup()
DELIVERING = Delivering()
DELIVERED = Delivered()
CANCELLED = Cancelled()

_STATES: dict[str, OrderState] = {
    state.status: state
    for state in (
        PENDING_PAYMENT,
        ACCEPTED,
        PREPARING,
        READY_FOR_PICKUP,
        DELIVERING,
        DELIVERED,
        CANCELLED,
    )
}


def state_for(status: str) -> OrderState:
    """Rebuilds the state object from the persisted status string."""
    return _STATES[status]


def initial_state(pays_online: bool) -> OrderState:
    """Online payments wait for confirmation; cash orders go straight to the kitchen."""
    return PENDING_PAYMENT if pays_online else ACCEPTED
