from dataclasses import dataclass, field

from ..domain.catalog.menu import MenuSection, group_menu
from ..domain.catalog.queries import RestaurantQuery
from ..domain.catalog.rules import catalog_delivery_window, price_level
from ..domain.errors import NotFoundError
from ..models import Cuisine, Dish
from ..repositories import (
    CuisineRepository,
    CuisineWithCount,
    DishRepository,
    PageResult,
    RestaurantRepository,
    RestaurantStats,
)


@dataclass(frozen=True)
class RestaurantSummary:
    id: int
    name: str
    description: str
    address: str
    lat: float
    lng: float
    image_url: str | None
    cuisines: list[Cuisine]
    rating: float | None
    review_count: int
    price_level: int | None
    delivery_minutes_min: int
    delivery_minutes_max: int
    avg_prep_minutes: int
    min_order_amount: int


@dataclass(frozen=True)
class RestaurantDetails(RestaurantSummary):
    # Number of reviews per star value 1..5, always all five keys.
    rating_breakdown: dict[int, int] = field(default_factory=dict)


class CatalogService:
    """Read side of the catalog: listing with filters, restaurant page, menu, cuisines."""

    def __init__(
        self,
        restaurants: RestaurantRepository,
        dishes: DishRepository,
        cuisines: CuisineRepository,
    ) -> None:
        self._restaurants = restaurants
        self._dishes = dishes
        self._cuisines = cuisines

    def list_restaurants(self, query: RestaurantQuery) -> PageResult[RestaurantSummary]:
        page = self._restaurants.search(query)
        return PageResult(
            items=[self._summary(stats) for stats in page.items],
            total=page.total,
            page=page.page,
            per_page=page.per_page,
        )

    def get_restaurant(self, restaurant_id: int) -> RestaurantDetails:
        stats = self._require_active(restaurant_id)
        counts = self._restaurants.rating_breakdown(restaurant_id)
        return RestaurantDetails(
            **vars(self._summary(stats)),
            rating_breakdown={star: counts.get(star, 0) for star in range(1, 6)},
        )

    def get_menu(self, restaurant_id: int) -> list[MenuSection[Dish]]:
        self._require_active(restaurant_id)
        return group_menu(self._dishes.list_for_restaurant(restaurant_id))

    def list_cuisines(self) -> list[CuisineWithCount]:
        return self._cuisines.list_with_counts()

    def _require_active(self, restaurant_id: int) -> RestaurantStats:
        stats = self._restaurants.get_active_with_stats(restaurant_id)
        if stats is None:
            raise NotFoundError("Restaurant not found.", "RESTAURANT_NOT_FOUND")
        return stats

    @staticmethod
    def _summary(stats: RestaurantStats) -> RestaurantSummary:
        restaurant = stats.restaurant
        window = catalog_delivery_window(restaurant.avg_prep_minutes)
        return RestaurantSummary(
            id=restaurant.id,
            name=restaurant.name,
            description=restaurant.description,
            address=restaurant.address,
            lat=restaurant.lat,
            lng=restaurant.lng,
            image_url=restaurant.image_url,
            cuisines=sorted(restaurant.cuisines, key=lambda c: c.name),
            rating=round(stats.rating, 1) if stats.rating is not None else None,
            review_count=stats.review_count,
            price_level=price_level(stats.avg_dish_price),
            delivery_minutes_min=window.min_minutes,
            delivery_minutes_max=window.max_minutes,
            avg_prep_minutes=restaurant.avg_prep_minutes,
            min_order_amount=restaurant.min_order_amount,
        )
