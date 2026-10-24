"""Manual dependency injection: the one place that knows concrete classes.

Built once in the app factory; blueprints fetch ready services via
`get_services()` instead of constructing collaborators themselves (DIP).
"""

from dataclasses import dataclass

from flask import Config, current_app

from .domain.delivery.strategies import (
    DeliveryStrategyResolver,
    ExpressDelivery,
    PickupDelivery,
    StandardDelivery,
)
from .domain.orders.validation import build_order_validation_chain
from .extensions import db
from .repositories import (
    CuisineRepository,
    DishRepository,
    LoyaltyRepository,
    OrderRepository,
    RestaurantRepository,
    UserRepository,
)
from .services.auth_service import AuthService
from .services.catalog_service import CatalogService
from .services.checkout_facade import CheckoutFacade
from .services.order_service import OrderService
from .services.quote_service import OrderQuoteService

EXTENSION_KEY = "forkful_services"


@dataclass(frozen=True)
class Services:
    auth: AuthService
    catalog: CatalogService
    quotes: OrderQuoteService
    checkout: CheckoutFacade
    orders: OrderService


def build_services(config: Config) -> Services:
    session = db.session
    restaurants = RestaurantRepository(session)
    dishes = DishRepository(session)
    delivery_strategies = DeliveryStrategyResolver(
        [StandardDelivery(), ExpressDelivery(), PickupDelivery()]
    )
    loyalty = LoyaltyRepository(session)
    orders = OrderRepository(session)
    quotes = OrderQuoteService(
        restaurants,
        dishes,
        loyalty,
        delivery_strategies,
        validation_chain=build_order_validation_chain(),
        delivery_radius_km=config["DELIVERY_RADIUS_KM"],
    )
    return Services(
        auth=AuthService(UserRepository(session)),
        catalog=CatalogService(restaurants, dishes, CuisineRepository(session)),
        quotes=quotes,
        checkout=CheckoutFacade(quotes, orders, loyalty),
        orders=OrderService(orders),
    )


def get_services() -> Services:
    return current_app.extensions[EXTENSION_KEY]
