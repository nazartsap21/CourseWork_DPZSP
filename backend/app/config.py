import os
from datetime import timedelta

from dotenv import load_dotenv

# Loaded here so every entry point (flask CLI, run.py, seed.py) sees backend/.env.
load_dotenv()


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-key-change-me-0123456789")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-jwt-secret-change-me-0123456789")
    # No refresh tokens: one access token valid for a working day is enough here.
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv("JWT_ACCESS_TOKEN_HOURS", "12")))
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///forkful.db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Couriers deliver within this straight-line radius from the restaurant.
    DELIVERY_RADIUS_KM = float(os.getenv("DELIVERY_RADIUS_KM", "7"))
    # Test-mode key (sk_test_...). Empty: card payments use the mock gateway.
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
    # Where payment providers send the customer back after paying.
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
    # Road routes for couriers; falls back to a straight line if unreachable.
    OSRM_BASE_URL = os.getenv("OSRM_BASE_URL", "https://router.project-osrm.org")
    JSON_SORT_KEYS = False


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


config: dict[str, type[BaseConfig]] = {
    "default": DevelopmentConfig,
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
