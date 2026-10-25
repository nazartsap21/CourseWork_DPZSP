import logging

from flask import Flask

from . import models  # noqa: F401  (registers tables for Alembic)
from .api.errors import register_error_handlers
from .api.v1 import api_v1_bp
from .config import config
from .container import EXTENSION_KEY, build_services, register_order_observers
from .domain.events.publisher import OrderEventPublisher
from .extensions import db, jwt, migrate


def _configure_app_logging() -> None:
    """Our own loggers (e.g. `forkful.commands`) print INFO; libraries keep their defaults."""
    logger = logging.getLogger("forkful")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)


def create_app(config_name: str = "default") -> Flask:
    _configure_app_logging()
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    app.extensions[EXTENSION_KEY] = build_services(app.config)
    register_order_observers(OrderEventPublisher.instance())
    register_error_handlers(app, jwt)
    app.register_blueprint(api_v1_bp)

    @app.get("/")
    def index():
        return {"app": "forkful", "status": "ok"}

    return app
