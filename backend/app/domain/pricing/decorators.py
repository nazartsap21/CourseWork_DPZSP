"""Decorator pattern for the order price.

`BaseOrderPrice` knows only the dishes subtotal and the delivery fee. Each
discount wraps another `PriceComponent`, adds its own adjustment to the total
and its own line to the breakdown. Discounts combine freely per customer
(regular + premium, premium only, points only, ...) without a class for every
combination, and the order of wrapping defines the order of application.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class PriceLine:
    """One row of the checkout breakdown. `amount` is signed kopiyky (discounts < 0)."""

    code: str
    label: str
    amount: int


class PriceComponent(ABC):
    """Anything that can report a total and the lines that explain it."""

    @abstractmethod
    def subtotal(self) -> int:
        """Dishes only, before any adjustment."""

    @abstractmethod
    def delivery_fee(self) -> int:
        """Delivery fee as charged after adjustments made so far."""

    @abstractmethod
    def total(self) -> int: ...

    @abstractmethod
    def lines(self) -> list[PriceLine]: ...

    def bonus_points_used(self) -> int:
        return 0


class BaseOrderPrice(PriceComponent):
    def __init__(self, subtotal: int, delivery_fee: int) -> None:
        self._subtotal = subtotal
        self._delivery_fee = delivery_fee

    def subtotal(self) -> int:
        return self._subtotal

    def delivery_fee(self) -> int:
        return self._delivery_fee

    def total(self) -> int:
        return self._subtotal + self._delivery_fee

    def lines(self) -> list[PriceLine]:
        return [
            PriceLine("subtotal", "Dishes", self._subtotal),
            PriceLine("delivery", "Delivery", self._delivery_fee),
        ]


class PriceDecorator(PriceComponent):
    """Delegates everything to the wrapped component; subclasses add one adjustment."""

    def __init__(self, inner: PriceComponent) -> None:
        self._inner = inner

    def subtotal(self) -> int:
        return self._inner.subtotal()

    def delivery_fee(self) -> int:
        return self._inner.delivery_fee()

    def bonus_points_used(self) -> int:
        return self._inner.bonus_points_used()

    def total(self) -> int:
        return self._inner.total() + self.adjustment()

    def lines(self) -> list[PriceLine]:
        own = self.line()
        return [*self._inner.lines(), *([own] if own.amount else [])]

    @abstractmethod
    def adjustment(self) -> int:
        """Signed change to the total, in kopiyky."""

    @abstractmethod
    def line(self) -> PriceLine: ...


class RegularCustomerDiscount(PriceDecorator):
    """Percentage off the dishes (not the delivery) for customers past the order threshold."""

    def __init__(self, inner: PriceComponent, percent: int) -> None:
        super().__init__(inner)
        self._percent = percent

    def adjustment(self) -> int:
        return -(self.subtotal() * self._percent // 100)

    def line(self) -> PriceLine:
        return PriceLine(
            "regular_discount", f"Regular customer −{self._percent}%", self.adjustment()
        )


class PremiumFreeDelivery(PriceDecorator):
    """Premium card holders don't pay for delivery, whatever the method."""

    def adjustment(self) -> int:
        return -self._inner.delivery_fee()

    def delivery_fee(self) -> int:
        return 0

    def line(self) -> PriceLine:
        return PriceLine("premium_free_delivery", "Premium card: free delivery", self.adjustment())


class BonusPointsRedemption(PriceDecorator):
    """Pays part of the order with points. Applied last, so it can never push the
    total below zero or above the redemption cap after other discounts."""

    def __init__(self, inner: PriceComponent, points: int, point_value: int, max_percent: int):
        super().__init__(inner)
        cap_amount = min(inner.subtotal() * max_percent // 100, inner.total())
        affordable = cap_amount // point_value if point_value else 0
        self._points = max(min(points, affordable), 0)
        self._point_value = point_value

    def bonus_points_used(self) -> int:
        return self._inner.bonus_points_used() + self._points

    def adjustment(self) -> int:
        return -(self._points * self._point_value)

    def line(self) -> PriceLine:
        return PriceLine("bonus_points", f"Bonus points ({self._points})", self.adjustment())


@dataclass(frozen=True)
class PriceBreakdown:
    """Final numbers, in the shape the Order model stores them.

    `delivery_fee` is what is charged (0 with premium); `discount` is the sum of
    the other reductions (regular discount and points)."""

    subtotal: int
    delivery_fee: int
    discount: int
    bonus_points_used: int
    total: int
    lines: list[PriceLine]

    @classmethod
    def from_component(cls, price: PriceComponent) -> "PriceBreakdown":
        total = price.total()
        delivery_fee = price.delivery_fee()
        return cls(
            subtotal=price.subtotal(),
            delivery_fee=delivery_fee,
            discount=price.subtotal() + delivery_fee - total,
            bonus_points_used=price.bonus_points_used(),
            total=total,
            lines=price.lines(),
        )
