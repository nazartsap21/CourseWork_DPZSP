from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from ..domain.delivery.geo import GeoPoint
from ..domain.delivery.strategies import DeliveryContext, DeliveryQuote, DeliveryStrategyResolver
from ..domain.errors import BusinessRuleError, NotFoundError
from ..domain.orders.builder import DishSnapshot, OrderBuilder, OrderDraft, RestaurantSnapshot
from ..domain.orders.validation import (
    OrderValidationContext,
    OrderValidationError,
    OrderValidator,
)
from ..domain.pricing.decorators import PriceBreakdown
from ..domain.pricing.loyalty import (
    GUEST_LOYALTY,
    LoyaltyRules,
    LoyaltyStatus,
    loyalty_status,
    max_redeemable_points,
)
from ..domain.pricing.policy import calculate_order_price
from ..models import Dish, LoyaltyAccount, LoyaltySettings, Restaurant
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
    # Only needed when the quote is turned into a real order at checkout.
    delivery_address: str | None = None
    delivery_note: str | None = None
    payment_method: str | None = None


@dataclass(frozen=True)
class Quote:
    draft: OrderDraft
    delivery: DeliveryQuote
    price: PriceBreakdown
    loyalty: LoyaltyStatus
    max_redeemable_points: int
    delivery_radius_km: float
    # First broken business rule, if any. A quote is still priced so the
    # checkout can show the numbers next to the problem.
    validation_error: OrderValidationError | None


def _rules(settings: LoyaltySettings) -> LoyaltyRules:
    return LoyaltyRules(
        points_per_100_uah=settings.points_per_100_uah,
        point_value=settings.point_value,
        max_points_redemption_percent=settings.max_points_redemption_percent,
        regular_customer_threshold=settings.regular_customer_threshold,
        regular_customer_discount_percent=settings.regular_customer_discount_percent,
    )


def _restaurant_snapshot(restaurant: Restaurant) -> RestaurantSnapshot:
    return RestaurantSnapshot(
        id=restaurant.id,
        name=restaurant.name,
        is_active=restaurant.is_active,
        location=GeoPoint(restaurant.lat, restaurant.lng),
        prep_minutes=restaurant.avg_prep_minutes,
        min_order_amount=restaurant.min_order_amount,
    )


def _dish_snapshot(dish: Dish) -> DishSnapshot:
    return DishSnapshot(
        id=dish.id,
        restaurant_id=dish.restaurant_id,
        name=dish.name,
        price=dish.price,
        is_available=dish.is_available,
    )


class OrderQuoteService:
    """Prices and validates a prospective order.

    Assembles it with `OrderBuilder`, prices delivery with the matching
    `DeliveryStrategy`, applies discounts through the `PriceComponent`
    decorators and runs the `OrderValidator` chain. Used by `POST /orders/quote`
    and later by checkout, so the quoted and the charged price come from the
    same code.
    """

    def __init__(
        self,
        restaurants: RestaurantRepository,
        dishes: DishRepository,
        loyalty: LoyaltyRepository,
        delivery_strategies: DeliveryStrategyResolver,
        validation_chain: OrderValidator,
        delivery_radius_km: float,
        clock: Callable[[], datetime] = utcnow,
    ) -> None:
        self._restaurants = restaurants
        self._dishes = dishes
        self._loyalty = loyalty
        self._delivery_strategies = delivery_strategies
        self._validation_chain = validation_chain
        self._delivery_radius_km = delivery_radius_km
        self._clock = clock

    def quote(self, request: QuoteRequest, customer_id: int | None) -> Quote:
        draft = self._build_draft(request, customer_id)

        strategy = self._delivery_strategies.resolve(draft.delivery.method)
        delivery = strategy.quote(
            DeliveryContext(
                restaurant=draft.restaurant.location,
                prep_minutes=draft.restaurant.prep_minutes,
                destination=draft.delivery.destination if strategy.requires_address else None,
            )
        )

        rules = _rules(self._loyalty.get_settings())
        account = self._loyalty.get_account(customer_id) if customer_id is not None else None
        status = self._loyalty_status(account, rules)
        max_points = max_redeemable_points(rules, draft.subtotal, status.points_balance)

        try:
            self._validation_chain.validate(
                OrderValidationContext(
                    draft=draft,
                    requires_address=strategy.requires_address,
                    delivery_radius_km=self._delivery_radius_km,
                    has_loyalty_account=account is not None,
                    loyalty=status,
                    max_redeemable_points=max_points,
                )
            )
            validation_error = None
        except OrderValidationError as error:
            validation_error = error

        price = calculate_order_price(
            draft.subtotal, delivery.fee, status, rules, draft.requested_points
        )
        return Quote(
            draft=draft,
            delivery=delivery,
            price=price,
            loyalty=status,
            max_redeemable_points=max_points,
            delivery_radius_km=self._delivery_radius_km,
            validation_error=validation_error,
        )

    def _build_draft(self, request: QuoteRequest, customer_id: int | None) -> OrderDraft:
        restaurant = self._restaurants.get_by_id(request.restaurant_id)
        if restaurant is None:
            raise NotFoundError("Restaurant not found.", "RESTAURANT_NOT_FOUND")

        dish_ids = list({item.dish_id for item in request.items})
        dishes = {d.id: d for d in self._dishes.get_many_for_restaurant(restaurant.id, dish_ids)}
        missing = [dish_id for dish_id in dish_ids if dish_id not in dishes]
        if missing:
            # A reference to something that isn't on the menu is bad input, not a business
            # rule, so it fails right away instead of going through the chain.
            raise BusinessRuleError(
                f"Dishes {missing} are not on this restaurant's menu.",
                "DISH_NOT_FOUND",
                field="items",
            )

        builder = OrderBuilder(customer_id).for_restaurant(_restaurant_snapshot(restaurant))
        for item in request.items:
            builder.add_item(_dish_snapshot(dishes[item.dish_id]), item.quantity)
        builder.with_delivery(
            request.delivery_method,
            request.destination,
            request.delivery_address,
            request.delivery_note,
        ).redeem_points(request.bonus_points)
        if request.payment_method is not None:
            builder.with_payment(request.payment_method)
        return builder.build()

    def _loyalty_status(self, account: LoyaltyAccount | None, rules: LoyaltyRules) -> LoyaltyStatus:
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
