"""Chain of Responsibility for order validation.

Each handler checks one independent rule and either raises an
`OrderValidationError` (stopping the chain) or passes the context to the next
handler. Rules can be added, removed or reordered by changing how the chain is
linked in `build_order_validation_chain`, without touching the other handlers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..delivery.geo import haversine_km
from ..errors import BusinessRuleError
from ..pricing.loyalty import LoyaltyStatus
from .builder import OrderDraft


class OrderValidationError(BusinessRuleError):
    code = "ORDER_INVALID"


@dataclass(frozen=True)
class OrderValidationContext:
    """Everything the rules need, gathered once by the service."""

    draft: OrderDraft
    requires_address: bool
    delivery_radius_km: float
    has_loyalty_account: bool
    loyalty: LoyaltyStatus
    max_redeemable_points: int


class OrderValidator(ABC):
    """One link of the chain."""

    def __init__(self) -> None:
        self._next: OrderValidator | None = None

    def set_next(self, handler: "OrderValidator") -> "OrderValidator":
        """Links `handler` after this one and returns it, so links can be chained."""
        self._next = handler
        return handler

    def validate(self, context: OrderValidationContext) -> None:
        self.check(context)
        if self._next is not None:
            self._next.validate(context)

    @abstractmethod
    def check(self, context: OrderValidationContext) -> None:
        """Raise `OrderValidationError` if the rule is broken."""


class RestaurantActiveCheck(OrderValidator):
    def check(self, context: OrderValidationContext) -> None:
        restaurant = context.draft.restaurant
        if not restaurant.is_active:
            raise OrderValidationError(
                f"{restaurant.name} isn't taking orders right now.",
                "RESTAURANT_UNAVAILABLE",
                field="restaurant_id",
            )


class ItemsAvailableCheck(OrderValidator):
    def check(self, context: OrderValidationContext) -> None:
        unavailable = [item.dish.name for item in context.draft.items if not item.dish.is_available]
        if unavailable:
            names = ", ".join(unavailable)
            verb = "is" if len(unavailable) == 1 else "are"
            raise OrderValidationError(
                f"{names} {verb} sold out. Remove {'it' if len(unavailable) == 1 else 'them'} "
                "to continue.",
                "ITEMS_UNAVAILABLE",
                field="items",
            )


class MinOrderAmountCheck(OrderValidator):
    def check(self, context: OrderValidationContext) -> None:
        draft = context.draft
        missing = draft.restaurant.min_order_amount - draft.subtotal
        if missing > 0:
            raise OrderValidationError(
                f"Minimum order at {draft.restaurant.name} is "
                f"{draft.restaurant.min_order_amount / 100:g} ₴. Add {missing / 100:g} ₴ more.",
                "BELOW_MIN_ORDER",
                field="items",
            )


class DeliveryZoneCheck(OrderValidator):
    """Courier orders need a point within the radius (straight line from the restaurant)."""

    def check(self, context: OrderValidationContext) -> None:
        if not context.requires_address:
            return
        destination = context.draft.delivery.destination
        if destination is None:
            raise OrderValidationError(
                "Pick the delivery point on the map.",
                "DELIVERY_ADDRESS_REQUIRED",
                field="delivery_point",
            )
        distance = haversine_km(context.draft.restaurant.location, destination)
        if distance > context.delivery_radius_km:
            raise OrderValidationError(
                f"This address is {distance:.1f} km away; "
                f"{context.draft.restaurant.name} delivers within "
                f"{context.delivery_radius_km:g} km. Choose pickup or a closer point.",
                "OUTSIDE_DELIVERY_ZONE",
                field="delivery_point",
            )


class BonusPointsCheck(OrderValidator):
    def check(self, context: OrderValidationContext) -> None:
        requested = context.draft.requested_points
        if requested == 0:
            return
        if not context.has_loyalty_account:
            raise OrderValidationError(
                "Sign in as a customer to use bonus points.",
                "POINTS_REQUIRE_ACCOUNT",
                field="bonus_points",
            )
        if requested > context.loyalty.points_balance:
            raise OrderValidationError(
                f"You have {context.loyalty.points_balance} points.",
                "NOT_ENOUGH_POINTS",
                field="bonus_points",
            )
        if requested > context.max_redeemable_points:
            raise OrderValidationError(
                f"You can use up to {context.max_redeemable_points} points on this order.",
                "POINTS_LIMIT_EXCEEDED",
                field="bonus_points",
            )


def build_order_validation_chain() -> OrderValidator:
    """Cheap, most fundamental checks first: no point checking the address of
    an order from a closed restaurant."""
    head = RestaurantActiveCheck()
    (
        head.set_next(ItemsAvailableCheck())
        .set_next(MinOrderAmountCheck())
        .set_next(DeliveryZoneCheck())
        .set_next(BonusPointsCheck())
    )
    return head
