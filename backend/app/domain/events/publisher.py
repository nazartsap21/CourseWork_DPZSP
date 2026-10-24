"""Observer pattern subject, implemented as a Singleton.

When an order changes status, the code that changed it publishes one
`OrderStatusChanged` event and doesn't know who reacts: history logging,
customer notifications and (later) loyalty points are observers that
subscribe once in the app factory.

Why a Singleton: every service that changes orders (checkout, payments, staff
status changes, commands) must publish to the *same* subscriber list, or some
observers would silently miss events. One instance per process guarantees
that. Tradeoffs: it is global state (tests must `reset()` it), and two Flask
apps in one process would share observers, which this project never does.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar


@dataclass(frozen=True)
class OrderStatusChanged:
    """`old_status` is None when the order was just created."""

    order_id: int
    customer_id: int
    restaurant_name: str
    is_pickup: bool
    old_status: str | None
    new_status: str
    changed_by_id: int | None
    occurred_at: datetime


class OrderObserver(ABC):
    @abstractmethod
    def on_status_changed(self, event: OrderStatusChanged) -> None: ...


class OrderEventPublisher:
    """Keeps the observer list and notifies every observer of each event.

    Observers run synchronously inside the caller's transaction, so the status
    change and everything observers write are committed (or rolled back) together.
    """

    _instance: ClassVar["OrderEventPublisher | None"] = None
    _observers: list[OrderObserver]

    def __new__(cls) -> "OrderEventPublisher":
        # Any OrderEventPublisher() call returns the one shared instance.
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._observers = []
            cls._instance = instance
        return cls._instance

    @classmethod
    def instance(cls) -> "OrderEventPublisher":
        return cls()

    def subscribe(self, observer: OrderObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: OrderObserver) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def reset(self) -> None:
        """Drops all observers; the app factory calls it before subscribing."""
        self._observers.clear()

    def publish(self, event: OrderStatusChanged) -> None:
        for observer in list(self._observers):
            observer.on_status_changed(event)

    @property
    def observers(self) -> tuple[OrderObserver, ...]:
        return tuple(self._observers)
