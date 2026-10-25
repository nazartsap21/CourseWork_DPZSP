"""Command pattern for customer actions on past orders.

Each user action ("order this again", "cancel this order") is an object that
carries its parameters and knows how to execute itself. The `CommandInvoker`
runs any command the same way and records every execution (who, what, result,
duration) in a `CommandLog`, so the actions are auditable and the API layer
doesn't need to know what a command does internally.
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol

from ..errors import BusinessRuleError, DomainError, NotFoundError
from .builder import DishSnapshot

# ---------------------------------------------------------------- framework


class Command[ResultT](ABC):
    """One user action, ready to run."""

    name: str

    @abstractmethod
    def execute(self) -> ResultT: ...

    @abstractmethod
    def describe(self) -> dict[str, Any]:
        """Parameters worth recording in the execution log."""


@dataclass(frozen=True)
class CommandLogEntry:
    command: str
    actor_id: int
    params: dict[str, Any]
    succeeded: bool
    duration_ms: float
    error_code: str | None = None


class CommandLog(Protocol):
    def record(self, entry: CommandLogEntry) -> None: ...


class LoggerCommandLog:
    """Writes the execution log through Python logging (`forkful.commands`)."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger("forkful.commands")

    def record(self, entry: CommandLogEntry) -> None:
        outcome = "ok" if entry.succeeded else f"failed ({entry.error_code})"
        self._logger.info(
            "command=%s actor=%s params=%s outcome=%s duration_ms=%.1f",
            entry.command,
            entry.actor_id,
            entry.params,
            outcome,
            entry.duration_ms,
        )


class CommandInvoker:
    """Runs commands and records each execution, successful or not."""

    def __init__(self, log: CommandLog) -> None:
        self._log = log

    def run[ResultT](self, command: Command[ResultT], actor_id: int) -> ResultT:
        started = time.perf_counter()
        try:
            result = command.execute()
        except DomainError as error:
            self._record(command, actor_id, started, error.code)
            raise
        except Exception:
            self._record(command, actor_id, started, "UNEXPECTED_ERROR")
            raise
        self._record(command, actor_id, started, None)
        return result

    def _record(
        self, command: Command[Any], actor_id: int, started: float, error_code: str | None
    ) -> None:
        self._log.record(
            CommandLogEntry(
                command=command.name,
                actor_id=actor_id,
                params=command.describe(),
                succeeded=error_code is None,
                duration_ms=(time.perf_counter() - started) * 1000,
                error_code=error_code,
            )
        )


# ---------------------------------------------------------------- reorder


@dataclass(frozen=True)
class PastOrderItem:
    dish_id: int | None
    name: str
    price: int
    quantity: int


@dataclass(frozen=True)
class PastOrder:
    restaurant_id: int
    restaurant_name: str
    restaurant_active: bool
    restaurant_min_order: int
    items: list[PastOrderItem]


class PastOrders(Protocol):
    def past_order(self, order_id: int, customer_id: int) -> PastOrder | None: ...


class CurrentMenu(Protocol):
    def dish_snapshots(self, restaurant_id: int, dish_ids: list[int]) -> list[DishSnapshot]: ...


@dataclass(frozen=True)
class ReorderItem:
    dish_id: int
    name: str
    price: int
    quantity: int


@dataclass(frozen=True)
class SkippedItem:
    name: str
    reason: str


@dataclass(frozen=True)
class PriceChange:
    name: str
    old_price: int
    new_price: int


@dataclass(frozen=True)
class ReorderResult:
    """Cart contents rebuilt from a past order, at today's prices."""

    restaurant_id: int
    restaurant_name: str
    restaurant_min_order: int
    items: list[ReorderItem]
    skipped: list[SkippedItem] = field(default_factory=list)
    price_changes: list[PriceChange] = field(default_factory=list)


class ReorderCommand(Command[ReorderResult]):
    """Rebuilds a past order's cart from the current menu.

    Dishes that were removed or are sold out are skipped with a reason instead
    of failing the whole reorder; changed prices are reported so the customer
    isn't surprised at checkout. Nothing is ordered yet: the customer still
    confirms address and payment at checkout.
    """

    name = "reorder"

    def __init__(
        self, order_id: int, customer_id: int, past_orders: PastOrders, menu: CurrentMenu
    ) -> None:
        self._order_id = order_id
        self._customer_id = customer_id
        self._past_orders = past_orders
        self._menu = menu

    def describe(self) -> dict[str, Any]:
        return {"order_id": self._order_id}

    def execute(self) -> ReorderResult:
        past = self._past_orders.past_order(self._order_id, self._customer_id)
        if past is None:
            raise NotFoundError("Order not found.", "ORDER_NOT_FOUND")
        if not past.restaurant_active:
            raise BusinessRuleError(
                f"{past.restaurant_name} isn't taking orders right now.", "RESTAURANT_UNAVAILABLE"
            )

        dish_ids = [item.dish_id for item in past.items if item.dish_id is not None]
        current = {d.id: d for d in self._menu.dish_snapshots(past.restaurant_id, dish_ids)}
        items: list[ReorderItem] = []
        skipped: list[SkippedItem] = []
        price_changes: list[PriceChange] = []
        for item in past.items:
            dish = current.get(item.dish_id) if item.dish_id is not None else None
            if dish is None:
                skipped.append(SkippedItem(item.name, "no longer on the menu"))
            elif not dish.is_available:
                skipped.append(SkippedItem(dish.name, "sold out today"))
            else:
                if dish.price != item.price:
                    price_changes.append(PriceChange(dish.name, item.price, dish.price))
                items.append(ReorderItem(dish.id, dish.name, dish.price, item.quantity))

        if not items:
            raise BusinessRuleError(
                "None of the dishes from this order are available now.", "NOTHING_TO_REORDER"
            )
        return ReorderResult(
            restaurant_id=past.restaurant_id,
            restaurant_name=past.restaurant_name,
            restaurant_min_order=past.restaurant_min_order,
            items=items,
            skipped=skipped,
            price_changes=price_changes,
        )


# ---------------------------------------------------------------- cancel


class OrderCanceller[OrderT](Protocol):
    def cancel(self, order_id: int, actor_user_id: int, actor_role: str) -> OrderT: ...


class CancelOrderCommand[OrderT](Command[OrderT]):
    """Cancels an order. The receiver (`OrderService.cancel`) applies the State
    transition, refunds points and online payments and publishes the change;
    the command packages the request so the invoker can run and log it."""

    name = "cancel_order"

    def __init__(
        self, order_id: int, actor_user_id: int, actor_role: str, receiver: OrderCanceller[OrderT]
    ) -> None:
        self._order_id = order_id
        self._actor_user_id = actor_user_id
        self._actor_role = actor_role
        self._receiver = receiver

    def describe(self) -> dict[str, Any]:
        return {"order_id": self._order_id, "role": self._actor_role}

    def execute(self) -> OrderT:
        return self._receiver.cancel(self._order_id, self._actor_user_id, self._actor_role)
