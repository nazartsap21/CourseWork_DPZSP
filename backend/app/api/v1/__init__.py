from flask import Blueprint

from .auth import auth_bp
from .catalog import catalog_bp
from .health import health_bp
from .orders import orders_bp

api_v1_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")
api_v1_bp.register_blueprint(health_bp)
api_v1_bp.register_blueprint(auth_bp)
api_v1_bp.register_blueprint(catalog_bp)
api_v1_bp.register_blueprint(orders_bp)
