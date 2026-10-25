from flask import Blueprint, Response, jsonify

from ...container import get_services
from ...models import UserRole
from ...schemas.catalog import RestaurantSummaryOut
from ..security import current_user_id, roles_required

favorites_bp = Blueprint("favorites", __name__, url_prefix="/favorites")


@favorites_bp.get("")
@roles_required(UserRole.CUSTOMER)
def list_favorites() -> Response:
    restaurants = get_services().favorites.list(current_user_id())
    items = [RestaurantSummaryOut.model_validate(r).model_dump(mode="json") for r in restaurants]
    return jsonify({"items": items})


@favorites_bp.put("/<int:restaurant_id>")
@roles_required(UserRole.CUSTOMER)
def add_favorite(restaurant_id: int) -> tuple[str, int]:
    """Idempotent: adding an existing favorite is not an error."""
    get_services().favorites.add(current_user_id(), restaurant_id)
    return "", 204


@favorites_bp.delete("/<int:restaurant_id>")
@roles_required(UserRole.CUSTOMER)
def remove_favorite(restaurant_id: int) -> tuple[str, int]:
    get_services().favorites.remove(current_user_id(), restaurant_id)
    return "", 204
