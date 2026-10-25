"""Concrete observers of order status changes.

They write through small "sink" interfaces instead of importing the ORM, so
the domain layer stays persistence-agnostic; repositories implement the sinks.
"""

from typing import Protocol

from ..pricing.loyalty import LoyaltyRules, points_earned
from .publisher import OrderObserver, OrderStatusChanged


class StatusHistorySink(Protocol):
    def record_status(self, order_id: int, status: str, changed_by_id: int | None) -> None: ...


class NotificationSink(Protocol):
    def notify(self, user_id: int, type: str, message: str, order_id: int | None) -> None: ...


class LoyaltyLedger(Protocol):
    def rules(self) -> LoyaltyRules: ...

    def record_completed_order(self, customer_id: int, order_id: int, points: int) -> int | None:
        """Counts the order and credits points; returns the new balance (None: no account)."""
        ...


class StatusHistoryObserver(OrderObserver):
    """Keeps the audit trail: one history row per status change, with who made it."""

    def __init__(self, history: StatusHistorySink) -> None:
        self._history = history

    def on_status_changed(self, event: OrderStatusChanged) -> None:
        self._history.record_status(event.order_id, event.new_status, event.changed_by_id)


def status_message(event: OrderStatusChanged) -> str | None:
    """Customer-facing text for a status, or None when there is nothing worth telling."""
    order, place = f"Order #{event.order_id}", event.restaurant_name
    match event.new_status:
        case "accepted":
            return f"{order} from {place} is accepted. The kitchen starts soon."
        case "preparing":
            return f"{place} is preparing order #{event.order_id}."
        case "ready_for_pickup" if event.is_pickup:
            return f"{order} is ready. Pick it up at {place}."
        case "delivering":
            return f"{order} is on the way."
        case "delivered":
            verb = "collected" if event.is_pickup else "delivered"
            return f"{order} {verb}. Enjoy your meal!"
        case "cancelled":
            return f"{order} from {place} was cancelled."
    # Waiting for payment, and "ready" for courier orders, need no message.
    return None


class NotificationObserver(OrderObserver):
    """Tells the customer about status changes via in-app notifications."""

    TYPE = "order_status"

    def __init__(self, notifications: NotificationSink) -> None:
        self._notifications = notifications

    def on_status_changed(self, event: OrderStatusChanged) -> None:
        message = status_message(event)
        if message is not None:
            self._notifications.notify(event.customer_id, self.TYPE, message, event.order_id)


class LoyaltyObserver(OrderObserver):
    """Rewards delivered orders: points at the configured rate, one more completed
    order towards regular-customer status, and a notification with the new balance."""

    TYPE = "bonus_points"

    def __init__(self, ledger: LoyaltyLedger, notifications: NotificationSink) -> None:
        self._ledger = ledger
        self._notifications = notifications

    def on_status_changed(self, event: OrderStatusChanged) -> None:
        if event.new_status != "delivered":
            return
        points = points_earned(self._ledger.rules(), event.total)
        balance = self._ledger.record_completed_order(event.customer_id, event.order_id, points)
        if balance is not None and points > 0:
            self._notifications.notify(
                event.customer_id,
                self.TYPE,
                f"You earned {points} points for order #{event.order_id}. Balance: {balance}.",
                event.order_id,
            )
