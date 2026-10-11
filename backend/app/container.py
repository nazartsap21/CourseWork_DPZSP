"""Manual dependency injection: the one place that knows concrete classes.

Built once in the app factory; blueprints fetch ready services via
`get_services()` instead of constructing collaborators themselves (DIP).
"""

from dataclasses import dataclass

from flask import current_app

from .extensions import db
from .repositories import CuisineRepository, DishRepository, RestaurantRepository, UserRepository
from .services.auth_service import AuthService
from .services.catalog_service import CatalogService

EXTENSION_KEY = "forkful_services"


@dataclass(frozen=True)
class Services:
    auth: AuthService
    catalog: CatalogService


def build_services() -> Services:
    session = db.session
    return Services(
        auth=AuthService(UserRepository(session)),
        catalog=CatalogService(
            RestaurantRepository(session), DishRepository(session), CuisineRepository(session)
        ),
    )


def get_services() -> Services:
    return current_app.extensions[EXTENSION_KEY]
