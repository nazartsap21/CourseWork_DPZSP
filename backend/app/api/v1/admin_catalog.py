from typing import Any

from flask import Blueprint, Response, jsonify
from pydantic import BaseModel

from ...container import get_services
from ...models import Restaurant, UserRole
from ...schemas.admin_catalog import (
    AdminCuisineOut,
    AdminRestaurantListParams,
    AdminRestaurantOut,
    AdminRestaurantRowOut,
    CuisineIn,
    DishFields,
    DishPatch,
    RestaurantFields,
    RestaurantPatch,
)
from ...schemas.catalog import CuisineOut, DishOut
from ...schemas.common import Page
from ..security import roles_required
from ..validation import parse_body, parse_query

admin_catalog_bp = Blueprint("admin_catalog", __name__, url_prefix="/admin")

# Fields that may be cleared by sending null; everything else ignores nulls in a PATCH.
NULLABLE_FIELDS = {"image_url"}


@admin_catalog_bp.before_request
@roles_required(UserRole.ADMIN)
def require_admin() -> None:
    """Every route in this blueprint is admin-only."""


def _changes(patch: BaseModel) -> dict[str, Any]:
    """Only the fields the client actually sent."""
    return {
        field: value
        for field, value in patch.model_dump(exclude_unset=True).items()
        if value is not None or field in NULLABLE_FIELDS
    }


def _restaurant(restaurant: Restaurant) -> dict:
    return AdminRestaurantOut.model_validate(restaurant).model_dump(mode="json")


# ---- cuisines


@admin_catalog_bp.get("/cuisines")
def list_cuisines() -> Response:
    items = [
        AdminCuisineOut(id=c.cuisine.id, name=c.cuisine.name, restaurant_count=c.restaurant_count)
        for c in get_services().admin_catalog.list_cuisines()
    ]
    return jsonify({"items": [item.model_dump() for item in items]})


@admin_catalog_bp.post("/cuisines")
def create_cuisine() -> tuple[Response, int]:
    cuisine = get_services().admin_catalog.create_cuisine(parse_body(CuisineIn).name)
    return jsonify(CuisineOut.model_validate(cuisine).model_dump()), 201


@admin_catalog_bp.patch("/cuisines/<int:cuisine_id>")
def rename_cuisine(cuisine_id: int) -> Response:
    cuisine = get_services().admin_catalog.rename_cuisine(cuisine_id, parse_body(CuisineIn).name)
    return jsonify(CuisineOut.model_validate(cuisine).model_dump())


@admin_catalog_bp.delete("/cuisines/<int:cuisine_id>")
def delete_cuisine(cuisine_id: int) -> tuple[str, int]:
    get_services().admin_catalog.delete_cuisine(cuisine_id)
    return "", 204


# ---- restaurants


@admin_catalog_bp.get("/restaurants")
def list_restaurants() -> Response:
    params = parse_query(AdminRestaurantListParams)
    result = get_services().admin_catalog.list_restaurants(
        params.q, params.active, params.page, params.per_page
    )
    page = Page[AdminRestaurantRowOut](
        items=[
            AdminRestaurantRowOut.model_validate(
                {
                    **AdminRestaurantOut.model_validate(row.restaurant).model_dump(),
                    "dish_count": row.dish_count,
                }
            )
            for row in result.items
        ],
        total=result.total,
        page=result.page,
        per_page=result.per_page,
        pages=result.pages,
    )
    return jsonify(page.model_dump(mode="json"))


@admin_catalog_bp.get("/restaurants/<int:restaurant_id>")
def get_restaurant(restaurant_id: int) -> Response:
    return jsonify(_restaurant(get_services().admin_catalog.get_restaurant(restaurant_id)))


@admin_catalog_bp.post("/restaurants")
def create_restaurant() -> tuple[Response, int]:
    fields = parse_body(RestaurantFields).model_dump()
    return jsonify(_restaurant(get_services().admin_catalog.create_restaurant(fields))), 201


@admin_catalog_bp.patch("/restaurants/<int:restaurant_id>")
def update_restaurant(restaurant_id: int) -> Response:
    changes = _changes(parse_body(RestaurantPatch))
    restaurant = get_services().admin_catalog.update_restaurant(restaurant_id, changes)
    return jsonify(_restaurant(restaurant))


@admin_catalog_bp.delete("/restaurants/<int:restaurant_id>")
def delete_restaurant(restaurant_id: int) -> tuple[str, int]:
    get_services().admin_catalog.delete_restaurant(restaurant_id)
    return "", 204


# ---- dishes


@admin_catalog_bp.get("/restaurants/<int:restaurant_id>/dishes")
def list_dishes(restaurant_id: int) -> Response:
    dishes = get_services().admin_catalog.list_dishes(restaurant_id)
    return jsonify({"items": [DishOut.model_validate(d).model_dump(mode="json") for d in dishes]})


@admin_catalog_bp.post("/restaurants/<int:restaurant_id>/dishes")
def create_dish(restaurant_id: int) -> tuple[Response, int]:
    fields = parse_body(DishFields).model_dump()
    dish = get_services().admin_catalog.create_dish(restaurant_id, fields)
    return jsonify(DishOut.model_validate(dish).model_dump(mode="json")), 201


@admin_catalog_bp.patch("/dishes/<int:dish_id>")
def update_dish(dish_id: int) -> Response:
    dish = get_services().admin_catalog.update_dish(dish_id, _changes(parse_body(DishPatch)))
    return jsonify(DishOut.model_validate(dish).model_dump(mode="json"))


@admin_catalog_bp.delete("/dishes/<int:dish_id>")
def delete_dish(dish_id: int) -> tuple[str, int]:
    get_services().admin_catalog.delete_dish(dish_id)
    return "", 204
