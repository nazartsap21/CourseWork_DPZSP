from ..domain.errors import NotFoundError
from ..models import Favorite
from ..repositories import FavoriteRepository, RestaurantRepository
from .catalog_service import CatalogService, RestaurantSummary


class FavoritesService:
    """A customer's favorite restaurants. Adding and removing are idempotent,
    so a double click on the heart can't fail or create duplicates."""

    def __init__(
        self,
        favorites: FavoriteRepository,
        restaurants: RestaurantRepository,
        catalog: CatalogService,
    ) -> None:
        self._favorites = favorites
        self._restaurants = restaurants
        self._catalog = catalog

    def list(self, customer_id: int) -> list[RestaurantSummary]:
        return self._catalog.list_by_ids(self._favorites.restaurant_ids(customer_id))

    def add(self, customer_id: int, restaurant_id: int) -> None:
        restaurant = self._restaurants.get_by_id(restaurant_id)
        if restaurant is None or not restaurant.is_active:
            raise NotFoundError("Restaurant not found.", "RESTAURANT_NOT_FOUND")
        if not self._favorites.exists(customer_id, restaurant_id):
            self._favorites.add(Favorite(customer_id=customer_id, restaurant_id=restaurant_id))
            self._favorites.commit()

    def remove(self, customer_id: int, restaurant_id: int) -> None:
        self._favorites.remove(customer_id, restaurant_id)
        self._favorites.commit()
