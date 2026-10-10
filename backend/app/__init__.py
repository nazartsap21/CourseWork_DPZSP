from flask import Flask

from .api.v1 import api_v1_bp
from .config import config
from .extensions import db, jwt, migrate


def create_app(config_name: str = "default") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(api_v1_bp)

    @app.get("/")
    def index():
        return {"app": "forkful", "status": "ok"}

    return app
