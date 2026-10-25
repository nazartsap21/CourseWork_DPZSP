from flask import Blueprint, Response, jsonify

from ...container import get_services
from ...domain.catalog.queries import RestaurantQuery
from ...schemas.catalog import (
    CuisineWithCountOut,
    MenuOut,
    MenuSectionOut,
    RestaurantDetailsOut,
    RestaurantListParams,
    RestaurantSummaryOut,
)
from ...schemas.common import Page, PageParams
from ...schemas.reviews import PublicReviewOut
from ..validation import parse_query

catalog_bp = Blueprint("catalog", __name__)


@catalog_bp.get("/cuisines")
def list_cuisines() -> Response:
    cuisines = get_services().catalog.list_cuisines()
    items = [
        CuisineWithCountOut(
            id=c.cuisine.id, name=c.cuisine.name, restaurant_count=c.restaurant_count
        )
        for c in cuisines
    ]
    return jsonify({"items": [item.model_dump() for item in items]})


@catalog_bp.get("/restaurants")
def list_restaurants() -> Response:
    params = parse_query(RestaurantListParams)
    result = get_services().catalog.list_restaurants(
        RestaurantQuery(
            cuisine_ids=params.cuisine,
            price_levels=params.price_level,
            max_delivery_minutes=params.max_delivery_minutes,
            min_rating=params.min_rating,
            sort=params.sort,
            page=params.page,
            per_page=params.per_page,
        )
    )
    page = Page[RestaurantSummaryOut](
        items=[RestaurantSummaryOut.model_validate(item) for item in result.items],
        total=result.total,
        page=result.page,
        per_page=result.per_page,
        pages=result.pages,
    )
    return jsonify(page.model_dump(mode="json"))


@catalog_bp.get("/restaurants/<int:restaurant_id>")
def get_restaurant(restaurant_id: int) -> Response:
    details = get_services().catalog.get_restaurant(restaurant_id)
    return jsonify(RestaurantDetailsOut.model_validate(details).model_dump(mode="json"))


@catalog_bp.get("/restaurants/<int:restaurant_id>/menu")
def get_menu(restaurant_id: int) -> Response:
    sections = get_services().catalog.get_menu(restaurant_id)
    menu = MenuOut(
        restaurant_id=restaurant_id,
        sections=[MenuSectionOut.model_validate(section) for section in sections],
    )
    return jsonify(menu.model_dump(mode="json"))


@catalog_bp.get("/restaurants/<int:restaurant_id>/reviews")
def list_reviews(restaurant_id: int) -> Response:
    """Newest first, paginated (`?page=&per_page=`)."""
    params = parse_query(PageParams)
    result = get_services().reviews.for_restaurant(restaurant_id, params.page, params.per_page)
    page = Page[PublicReviewOut](
        items=[PublicReviewOut.from_review(review) for review in result.items],
        total=result.total,
        page=result.page,
        per_page=result.per_page,
        pages=result.pages,
    )
    return jsonify(page.model_dump(mode="json"))
