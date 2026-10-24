"""State pattern for the order lifecycle.

Each status is a class that decides which actions are allowed from it and
which state each action leads to. An action that isn't allowed raises
`InvalidTransitionError` (HTTP 409), so invalid moves like "deliver a
cancelled order" are impossible by construction, not by scattered `if`s.

Transitions (action: from → to):
    pay:             pending_payment → accepted
    start_preparing: accepted → preparing
    mark_ready:      preparing → ready_for_pickup
    pick_up:         ready_for_pickup → delivering   (courier orders only)
    deliver:         delivering → delivered,
                     ready_for_pickup → delivered    (pickup orders skip delivering)
    cancel:          pending_payment | accepted → cancelled

States hold no per-order data, so one instance per status is shared
(`state_for`). Facts about the specific order that change the rules (pickup
or courier) are passed in as `OrderFacts`.
"""

from abc import ABC
from dataclasses import dataclass

from ..errors import ConflictError


class InvalidTransitionError(ConflictError):
    code = "INVALID_STATUS_TRANSITION"


@dataclass(frozen=True)
class OrderFacts:
    """Per-order information some transitions depend on."""

    is_pickup: bool


# Every action an order can receive, in lifecycle order.
ACTIONS = ("pay", "start_preparing", "mark_ready", "pick_up", "deliver", "cancel")


class OrderState(ABC):
    """Base state: every action is refused unless a subclass allows it."""

    status: str
    label: str

    def pay(self, facts: OrderFacts) -> "OrderState":
        raise self._refuse("confirm payment for")

    def start_preparing(self, facts: OrderFacts) -> "OrderState":
        raise self._refuse("start preparing")

    def mark_ready(self, facts: OrderFacts) -> "OrderState":
        raise self._refuse("mark as ready")

    def pick_up(self, facts: OrderFacts) -> "OrderState":
        raise self._refuse("hand to a courier")

    def deliver(self, facts: OrderFacts) -> "OrderState":
        raise self._refuse("mark as delivered")

    def cancel(self, facts: OrderFacts) -> "OrderState":
        raise self._refuse("cancel")

    def apply(self, action: str, facts: OrderFacts) -> "OrderState":
        if action not in ACTIONS:
            raise ValueError(f"Unknown order action: {action}")
        return getattr(self, action)(facts)

    def available_actions(self, facts: OrderFacts) -> dict[str, "OrderState"]:
        """Action → resulting state, for every action this state allows.

        Derived by trying each action, so the list can never disagree with
        the transition methods themselves."""
        available: dict[str, OrderState] = {}
        for action in ACTIONS:
            try:
                available[action] = self.apply(action, facts)
            except InvalidTransitionError:
                continue
        return available

    @property
    def is_final(self) -> bool:
        return False

    def _refuse(self, action: str) -> InvalidTransitionError:
        return InvalidTransitionError(f"Can't {action} an order that is {self.label.lower()}.")


class PendingPayment(OrderState):
    status = "pending_payment"
    label = "Waiting for payment"

    def pay(self, facts: OrderFacts) -> OrderState:
        return ACCEPTED

    def cancel(self, facts: OrderFacts) -> OrderState:
        return CANCELLED


class Accepted(OrderState):
    status = "accepted"
    label = "Accepted"

    def start_preparing(self, facts: OrderFacts) -> OrderState:
        return PREPARING

    def cancel(self, facts: OrderFacts) -> OrderState:
        return CANCELLED


class Preparing(OrderState):
    status = "preparing"
    label = "Preparing"

    def mark_ready(self, facts: OrderFacts) -> OrderState:
        return READY_FOR_PICKUP


class ReadyForPickup(OrderState):
    """Waits for a courier, or for the customer if it's a pickup order."""

    status = "ready_for_pickup"
    label = "Ready for pickup"

    def pick_up(self, facts: OrderFacts) -> OrderState:
        if facts.is_pickup:
            raise InvalidTransitionError(
                "Pickup orders are collected by the customer, not a courier."
            )
        return DELIVERING

    def deliver(self, facts: OrderFacts) -> OrderState:
        # Pickup orders skip Delivering: handing the bag over completes them.
        if not facts.is_pickup:
            raise InvalidTransitionError("A courier must pick the order up before delivering it.")
        return DELIVERED


class Delivering(OrderState):
    status = "delivering"
    label = "On the way"

    def deliver(self, facts: OrderFacts) -> OrderState:
        return DELIVERED


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
