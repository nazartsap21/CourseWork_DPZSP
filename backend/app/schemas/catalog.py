from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from ..domain.catalog.queries import RestaurantSort
from ..domain.catalog.rules import MAX_PRICE_LEVEL
from .common import PageParams


def _split_list(value: Any) -> Any:
    """Accepts both `?cuisine=1&cuisine=2` and `?cuisine=1,2`."""
    items = value if isinstance(value, list) else [value]
    return [part for item in items for part in str(item).split(",") if part.strip()]


IdList = Annotated[list[Annotated[int, Field(ge=1)]], BeforeValidator(_split_list)]
PriceLevelList = Annotated[
    list[Annotated[int, Field(ge=1, le=MAX_PRICE_LEVEL)]], BeforeValidator(_split_list)
]


class RestaurantListParams(PageParams):
    cuisine: IdList = []
    price_level: PriceLevelList = []
    max_delivery_minutes: int | None = Field(default=None, ge=1, le=240)
    min_rating: float | None = Field(default=None, ge=1, le=5)
    sort: RestaurantSort = RestaurantSort.RATING


class CuisineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class CuisineWithCountOut(CuisineOut):
    restaurant_count: int


class RestaurantSummaryOut(BaseModel):
    """Money fields (`min_order_amount`) are integer kopiyky."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    address: str
    lat: float
    lng: float
    image_url: str | None
    cuisines: list[CuisineOut]
    rating: float | None
    review_count: int
    price_level: int | None
    delivery_minutes_min: int
    delivery_minutes_max: int
    avg_prep_minutes: int
    min_order_amount: int


class RestaurantDetailsOut(RestaurantSummaryOut):
    rating_breakdown: dict[int, int]


class DishOut(BaseModel):
    """`price` is integer kopiyky."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    name: str
    description: str
    price: int
    category: str
    is_available: bool
    image_url: str | None


class MenuSectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: str
    dishes: list[DishOut]


class MenuOut(BaseModel):
    restaurant_id: int
    sections: list[MenuSectionOut]
