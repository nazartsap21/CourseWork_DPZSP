"""Manual dependency injection: the one place that knows concrete classes.

Built once in the app factory; blueprints fetch ready services via
`get_services()` instead of constructing collaborators themselves (DIP).
"""

from dataclasses import dataclass

from flask import current_app

from .extensions import db
from .repositories import UserRepository
from .services.auth_service import AuthService

EXTENSION_KEY = "forkful_services"


@dataclass(frozen=True)
class Services:
    auth: AuthService


def build_services() -> Services:
    users = UserRepository(db.session)
    return Services(auth=AuthService(users))


def get_services() -> Services:
    return current_app.extensions[EXTENSION_KEY]
