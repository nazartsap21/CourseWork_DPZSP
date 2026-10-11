from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from ..domain.delivery.geo import GeoPoint
from ..domain.delivery.strategies import DeliveryContext, DeliveryQuote, DeliveryStrategyResolver
from ..domain.errors import BusinessRuleError, NotFoundError
from ..domain.pricing.decorators import PriceBreakdown
from ..domain.pricing.loyalty import (
    GUEST_LOYALTY,
    LoyaltyRules,
    LoyaltyStatus,
    loyalty_status,
    max_redeemable_points,
)
from ..domain.pricing.policy import calculate_order_price
from ..models import LoyaltySettings, Restaurant
from ..models.base import utcnow
from ..repositories import DishRepository, LoyaltyRepository, RestaurantRepository


@dataclass(frozen=True)
class QuoteItemRequest:
    dish_id: int
    quantity: int


@dataclass(frozen=True)
class QuoteRequest:
    restaurant_id: int
    items: list[QuoteItemRequest]
    delivery_method: str
    destination: GeoPoint | None = None
    bonus_points: int = 0


@dataclass(frozen=True)
class QuotedItem:
    """Prices come from the database, never from the client."""

    dish_id: int
    name: str
    price: int
    quantity: int
    is_available: bool

    @property
    def line_total(self) -> int:
        return self.price * self.quantity


@dataclass(frozen=True)
class Quote:
    restaurant: Restaurant
    items: list[QuotedItem]
    delivery: DeliveryQuote
    price: PriceBreakdown
    loyalty: LoyaltyStatus
    max_redeemable_points: int


def _rules(settings: LoyaltySettings) -> LoyaltyRules:
    return LoyaltyRules(
        points_per_100_uah=settings.points_per_100_uah,
        point_value=settings.point_value,
        max_points_redemption_percent=settings.max_points_redemption_percent,
        regular_customer_threshold=settings.regular_customer_threshold,
        regular_customer_discount_percent=settings.regular_customer_discount_percent,
    )


class OrderQuoteService:
    """Prices a prospective order: dishes from the DB, delivery via the matching
    `DeliveryStrategy`, discounts via the `PriceComponent` decorator chain.

    Used by `POST /orders/quote` now and by checkout later, so the price the
    customer sees and the price they are charged come from the same code.
    """

    def __init__(
        self,
        restaurants: RestaurantRepository,
        dishes: DishRepository,
        loyalty: LoyaltyRepository,
        delivery_strategies: DeliveryStrategyResolver,
        clock: Callable[[], datetime] = utcnow,
    ) -> None:
        self._restaurants = restaurants
        self._dishes = dishes
        self._loyalty = loyalty
        self._delivery_strategies = delivery_strategies
        self._clock = clock

    def quote(self, request: QuoteRequest, customer_id: int | None) -> Quote:
        restaurant = self._restaurants.get_active(request.restaurant_id)
        if restaurant is None:
            raise NotFoundError("Restaurant not found.", "RESTAURANT_NOT_FOUND")

        items = self._price_items(restaurant.id, request.items)
        subtotal = sum(item.line_total for item in items)

        strategy = self._delivery_strategies.resolve(request.delivery_method)
        delivery = strategy.quote(
            DeliveryContext(
                restaurant=GeoPoint(restaurant.lat, restaurant.lng),
                prep_minutes=restaurant.avg_prep_minutes,
                destination=request.destination if strategy.requires_address else None,
            )
        )

        rules = _rules(self._loyalty.get_settings())
        status = self._loyalty_status(customer_id, rules)
        price = calculate_order_price(subtotal, delivery.fee, status, rules, request.bonus_points)
        return Quote(
            restaurant=restaurant,
            items=items,
            delivery=delivery,
            price=price,
            loyalty=status,
            max_redeemable_points=max_redeemable_points(rules, subtotal, status.points_balance),
        )

    def _price_items(
        self, restaurant_id: int, requested: list[QuoteItemRequest]
    ) -> list[QuotedItem]:
        # The same dish sent twice is merged rather than rejected.
        quantities: dict[int, int] = {}
        for item in requested:
            quantities[item.dish_id] = quantities.get(item.dish_id, 0) + item.quantity

        dishes = {
            d.id: d for d in self._dishes.get_many_for_restaurant(restaurant_id, list(quantities))
        }
        missing = [dish_id for dish_id in quantities if dish_id not in dishes]
        if missing:
            raise BusinessRuleError(
                f"Dishes {missing} are not on this restaurant's menu.", "DISH_NOT_FOUND"
            )
        return [
            QuotedItem(
                dish_id=dish_id,
                name=dishes[dish_id].name,
                price=dishes[dish_id].price,
                quantity=quantity,
                is_available=dishes[dish_id].is_available,
            )
            for dish_id, quantity in quantities.items()
        ]

    def _loyalty_status(self, customer_id: int | None, rules: LoyaltyRules) -> LoyaltyStatus:
        account = self._loyalty.get_account(customer_id) if customer_id is not None else None
        if account is None:
            return GUEST_LOYALTY
        premium_until = account.premium_until
        # SQLite returns naive datetimes; values are always stored in UTC.
        if premium_until is not None and premium_until.tzinfo is None:
            premium_until = premium_until.replace(tzinfo=UTC)
        return loyalty_status(
            rules,
            completed_orders=account.completed_orders_count,
            card_type=account.card_type.value,
            premium_until=premium_until,
            points_balance=account.points_balance,
            now=self._clock(),
        )
