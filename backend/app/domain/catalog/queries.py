from dataclasses import dataclass, field
from enum import StrEnum


class RestaurantSort(StrEnum):
    RATING = "rating"
    DELIVERY_TIME = "delivery_time"
    PRICE = "price"


@dataclass(frozen=True)
class RestaurantQuery:
    """Catalog filters as a plain value object, so the repository doesn't depend
    on HTTP parsing and the service doesn't depend on SQL."""

    cuisine_ids: list[int] = field(default_factory=list)
    price_levels: list[int] = field(default_factory=list)
    max_delivery_minutes: int | None = None
    min_rating: float | None = None
    sort: RestaurantSort = RestaurantSort.RATING
    page: int = 1
    per_page: int = 12
