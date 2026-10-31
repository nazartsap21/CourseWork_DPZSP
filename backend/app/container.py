"""Manual dependency injection: the one place that knows concrete classes.

Built once in the app factory; blueprints fetch ready services via
`get_services()` instead of constructing collaborators themselves (DIP).
"""

from dataclasses import dataclass

import stripe
from flask import Config, current_app

from .domain.delivery.routing import (
    FallbackRouteProvider,
    OsrmRouteProvider,
    StraightLineRouteProvider,
)
from .domain.delivery.strategies import (
    DeliveryStrategyResolver,
    ExpressDelivery,
    PickupDelivery,
    StandardDelivery,
)
from .domain.events.observers import (
    LoyaltyObserver,
    NotificationObserver,
    StatusHistoryObserver,
)
from .domain.events.publisher import OrderEventPublisher
from .domain.orders.commands import CommandInvoker, LoggerCommandLog
from .domain.orders.validation import build_order_validation_chain
from .domain.payments.factory import PaymentGatewayFactory
from .domain.payments.stripe_adapter import StripeGateway
from .extensions import db
from .repositories import (
    CuisineRepository,
    DishRepository,
    FavoriteRepository,
    LoyaltyRepository,
    NotificationRepository,
    OrderRepository,
    PaymentRepository,
    RestaurantRepository,
    ReviewRepository,
    StatusHistoryRepository,
    UserRepository,
)
from .services.admin_catalog_service import AdminCatalogService
from .services.admin_operations_service import AdminOperationsService
from .services.auth_service import AuthService
from .services.catalog_service import CatalogService
from .services.checkout_facade import CheckoutFacade
from .services.courier_service import CourierService
from .services.favorites_service import FavoritesService
from .services.loyalty_service import LoyaltyService
from .services.notification_service import NotificationService
from .services.order_actions import OrderActions
from .services.order_service import OrderService
from .services.payment_service import PaymentService, ReturnUrls
from .services.quote_service import OrderQuoteService
from .services.review_service import ReviewService

EXTENSION_KEY = "forkful_services"


@dataclass(frozen=True)
class Services:
    auth: AuthService
    catalog: CatalogService
    quotes: OrderQuoteService
    checkout: CheckoutFacade
    orders: OrderService
    payments: PaymentService
    notifications: NotificationService
    courier: CourierService
    favorites: FavoritesService
    order_actions: OrderActions
    loyalty: LoyaltyService
    reviews: ReviewService
    admin_catalog: AdminCatalogService
    admin_operations: AdminOperationsService


def register_order_observers(publisher: OrderEventPublisher) -> None:
    """Subscribes every observer once. Called from the app factory; `reset()`
    first, so creating the app again doesn't register duplicates."""
    publisher.reset()
    publisher.subscribe(StatusHistoryObserver(StatusHistoryRepository(db.session)))
    publisher.subscribe(NotificationObserver(NotificationRepository(db.session)))
    publisher.subscribe(
        LoyaltyObserver(LoyaltyRepository(db.session), NotificationRepository(db.session))
    )


def build_services(config: Config) -> Services:
    session = db.session
    events = OrderEventPublisher.instance()
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
    # Adapter + fallback: a slow or unreachable OSRM never blocks a pick-up.
    routes = FallbackRouteProvider(
        OsrmRouteProvider(config["OSRM_BASE_URL"]), StraightLineRouteProvider()
    )
    stripe_key = config["STRIPE_SECRET_KEY"]
    gateways = PaymentGatewayFactory(
        stripe_gateway=(lambda: StripeGateway(stripe.StripeClient(stripe_key)))
        if stripe_key
        else None
    )
    payments = PaymentService(
        gateways,
        PaymentRepository(session),
        orders,
        ReturnUrls.for_frontend(config["FRONTEND_URL"]),
        events,
        loyalty,
    )
    cuisines = CuisineRepository(session)
    catalog = CatalogService(restaurants, dishes, cuisines)
    order_service = OrderService(orders, events, routes, loyalty, gateways)
    users = UserRepository(session)
    return Services(
        auth=AuthService(users),
        catalog=catalog,
        quotes=quotes,
        checkout=CheckoutFacade(quotes, orders, loyalty, payments, events),
        orders=order_service,
        payments=payments,
        notifications=NotificationService(NotificationRepository(session)),
        courier=CourierService(orders),
        favorites=FavoritesService(FavoriteRepository(session), restaurants, catalog),
        loyalty=LoyaltyService(loyalty, users, payments),
        reviews=ReviewService(ReviewRepository(session), orders, restaurants),
        admin_catalog=AdminCatalogService(restaurants, dishes, cuisines),
        admin_operations=AdminOperationsService(
            users, orders, loyalty, NotificationRepository(session)
        ),
        order_actions=OrderActions(
            CommandInvoker(LoggerCommandLog()), order_service, past_orders=orders, menu=dishes
        ),
    )


def get_services() -> Services:
    return current_app.extensions[EXTENSION_KEY]
