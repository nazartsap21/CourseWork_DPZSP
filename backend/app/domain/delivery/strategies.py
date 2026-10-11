"""Strategy pattern: each delivery option computes its fee and ETA its own way.

The order only knows its `delivery_method`; `DeliveryStrategyResolver` turns
that into a strategy object at runtime. Adding a new option (e.g. "scheduled")
means adding one class and registering it; nothing else changes (OCP).
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from math import ceil

from ..errors import BusinessRuleError
from .geo import GeoPoint, haversine_km

ROUTE_DETOUR_FACTOR = 1.3
COURIER_SPEED_KMH = 20
DEFAULT_RIDE_MINUTES = 15
ETA_SPREAD_MINUTES = 5


@dataclass(frozen=True)
class DeliveryContext:
    restaurant: GeoPoint
    prep_minutes: int
    destination: GeoPoint | None = None


@dataclass(frozen=True)
class DeliveryQuote:
    """`fee` is integer kopiyky; `distance_km` is None for pickup or an unknown address."""

    method: str
    fee: int
    eta_minutes_min: int
    eta_minutes_max: int
    distance_km: float | None
    needs_courier: bool
    is_priority: bool


def route_km(context: DeliveryContext) -> float | None:
    if context.destination is None:
        return None
    return haversine_km(context.restaurant, context.destination) * ROUTE_DETOUR_FACTOR


def ride_minutes(distance_km: float | None) -> int:
    if distance_km is None:
        return DEFAULT_RIDE_MINUTES
    return max(ceil(distance_km / COURIER_SPEED_KMH * 60), 1)


class DeliveryStrategy(ABC):
    """Computes fee and ETA for one delivery option."""

    method: str

    @abstractmethod
    def quote(self, context: DeliveryContext) -> DeliveryQuote: ...

    @property
    def requires_address(self) -> bool:
        return True


class CourierDelivery(DeliveryStrategy):
    """Shared fee formula for courier options: a base fee covers the first
    kilometres, every started kilometre after that costs extra."""

    def __init__(self, base_fee: int, included_km: float, per_km_fee: int) -> None:
        self._base_fee = base_fee
        self._included_km = included_km
        self._per_km_fee = per_km_fee

    def _fee(self, distance_km: float | None) -> int:
        if distance_km is None or distance_km <= self._included_km:
            return self._base_fee
        return self._base_fee + ceil(distance_km - self._included_km) * self._per_km_fee

    def _window(self, minutes: int) -> tuple[int, int]:
        return max(minutes - ETA_SPREAD_MINUTES, 1), minutes + ETA_SPREAD_MINUTES


class StandardDelivery(CourierDelivery):
    method = "standard"
    COURIER_WAIT_MINUTES = 10

    def __init__(self, base_fee: int = 4900, included_km: float = 3, per_km_fee: int = 800):
        super().__init__(base_fee, included_km, per_km_fee)

    def quote(self, context: DeliveryContext) -> DeliveryQuote:
        distance = route_km(context)
        eta = context.prep_minutes + self.COURIER_WAIT_MINUTES + ride_minutes(distance)
        low, high = self._window(eta)
        return DeliveryQuote(self.method, self._fee(distance), low, high, distance, True, False)


class ExpressDelivery(CourierDelivery):
    method = "express"
    KITCHEN_SPEEDUP = 0.75

    def __init__(self, base_fee: int = 8900, included_km: float = 3, per_km_fee: int = 1200):
        super().__init__(base_fee, included_km, per_km_fee)

    def quote(self, context: DeliveryContext) -> DeliveryQuote:
        distance = route_km(context)
        prep = ceil(context.prep_minutes * self.KITCHEN_SPEEDUP)
        low, high = self._window(prep + ride_minutes(distance))
        return DeliveryQuote(self.method, self._fee(distance), low, high, distance, True, True)


class PickupDelivery(DeliveryStrategy):
    method = "pickup"

    def quote(self, context: DeliveryContext) -> DeliveryQuote:
        prep = context.prep_minutes
        return DeliveryQuote(self.method, 0, prep, prep + ETA_SPREAD_MINUTES, None, False, False)

    @property
    def requires_address(self) -> bool:
        return False


class DeliveryStrategyResolver:
    """Selects the strategy for an order's delivery method at runtime."""

    def __init__(self, strategies: Iterable[DeliveryStrategy]) -> None:
        self._strategies = {strategy.method: strategy for strategy in strategies}

    def resolve(self, method: str) -> DeliveryStrategy:
        try:
            return self._strategies[method]
        except KeyError:
            raise BusinessRuleError(
                f"Delivery method '{method}' is not available.", "DELIVERY_METHOD_UNAVAILABLE"
            ) from None

    @property
    def methods(self) -> list[str]:
        return list(self._strategies)
