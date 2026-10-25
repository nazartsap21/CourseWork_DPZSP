from flask import Blueprint

from .auth import auth_bp
from .catalog import catalog_bp
from .courier import courier_bp
from .favorites import favorites_bp
from .health import health_bp
from .notifications import notifications_bp
from .orders import orders_bp
from .payments import payments_bp

api_v1_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")
api_v1_bp.register_blueprint(health_bp)
api_v1_bp.register_blueprint(auth_bp)
api_v1_bp.register_blueprint(catalog_bp)
api_v1_bp.register_blueprint(orders_bp)
api_v1_bp.register_blueprint(payments_bp)
api_v1_bp.register_blueprint(notifications_bp)
api_v1_bp.register_blueprint(courier_bp)
api_v1_bp.register_blueprint(favorites_bp)
