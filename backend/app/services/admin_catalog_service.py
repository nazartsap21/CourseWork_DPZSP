from dataclasses import dataclass
from typing import Any

from ..domain.errors import ConflictError, NotFoundError
from ..models import Cuisine, Dish, Restaurant
from ..repositories import (
    CuisineRepository,
    CuisineWithCount,
    DishRepository,
    PageResult,
    RestaurantRepository,
)


@dataclass(frozen=True)
class RestaurantRow:
    restaurant: Restaurant
    dish_count: int


class AdminCatalogService:
    """Admin management of cuisines, restaurants and dishes.

    Unlike `CatalogService` (the customer-facing read side) it sees inactive
    restaurants and unavailable dishes. Deactivating is the normal way to hide a
    restaurant; deleting is allowed only when no order references it, so order
    history stays intact.
    """

    def __init__(
        self,
        restaurants: RestaurantRepository,
        dishes: DishRepository,
        cuisines: CuisineRepository,
    ) -> None:
        self._restaurants = restaurants
        self._dishes = dishes
        self._cuisines = cuisines

    # ---- cuisines

    def list_cuisines(self) -> list[CuisineWithCount]:
        return self._cuisines.list_with_all_counts()

    def create_cuisine(self, name: str) -> Cuisine:
        self._ensure_cuisine_name_free(name)
        cuisine = Cuisine(name=name)
        self._cuisines.add(cuisine)
        self._cuisines.commit()
        return cuisine

    def rename_cuisine(self, cuisine_id: int, name: str) -> Cuisine:
        cuisine = self._cuisine(cuisine_id)
        self._ensure_cuisine_name_free(name, exclude_id=cuisine_id)
        cuisine.name = name
        self._cuisines.commit()
        return cuisine

    def delete_cuisine(self, cuisine_id: int) -> None:
        cuisine = self._cuisine(cuisine_id)
        if cuisine.restaurants:
            raise ConflictError(
                f"{len(cuisine.restaurants)} restaurant(s) still use this cuisine.",
                "CUISINE_IN_USE",
            )
        self._cuisines.delete(cuisine)
        self._cuisines.commit()

    # ---- restaurants

    def list_restaurants(
        self, query: str, active: bool | None, page: int, per_page: int
    ) -> PageResult[RestaurantRow]:
        result = self._restaurants.admin_page(query, active, page, per_page)
        return PageResult(
            items=[RestaurantRow(r, count) for r, count in result.items],
            total=result.total,
            page=result.page,
            per_page=result.per_page,
        )

    def get_restaurant(self, restaurant_id: int) -> Restaurant:
        restaurant = self._restaurants.get_by_id(restaurant_id)
        if restaurant is None:
            raise NotFoundError("Restaurant not found.", "RESTAURANT_NOT_FOUND")
        return restaurant

    def create_restaurant(self, fields: dict[str, Any]) -> Restaurant:
        cuisine_ids = fields.pop("cuisine_ids")
        self._ensure_restaurant_name_free(fields["name"])
        restaurant = Restaurant(**fields, cuisines=self._cuisines_by_ids(cuisine_ids))
        self._restaurants.add(restaurant)
        self._restaurants.commit()
        return restaurant

    def update_restaurant(self, restaurant_id: int, changes: dict[str, Any]) -> Restaurant:
        restaurant = self.get_restaurant(restaurant_id)
        if "name" in changes:
            self._ensure_restaurant_name_free(changes["name"], exclude_id=restaurant_id)
        if "cuisine_ids" in changes:
            restaurant.cuisines = self._cuisines_by_ids(changes.pop("cuisine_ids"))
        for field, value in changes.items():
            setattr(restaurant, field, value)
        self._restaurants.commit()
        return restaurant

    def delete_restaurant(self, restaurant_id: int) -> None:
        restaurant = self.get_restaurant(restaurant_id)
        if self._restaurants.has_orders(restaurant_id):
            raise ConflictError(
                "This restaurant has orders. Deactivate it instead to keep the history.",
                "RESTAURANT_HAS_ORDERS",
            )
        self._restaurants.delete(restaurant)
        self._restaurants.commit()

    # ---- dishes

    def list_dishes(self, restaurant_id: int) -> list[Dish]:
        self.get_restaurant(restaurant_id)
        return self._dishes.list_for_restaurant(restaurant_id)

    def create_dish(self, restaurant_id: int, fields: dict[str, Any]) -> Dish:
        self.get_restaurant(restaurant_id)
        self._ensure_dish_name_free(restaurant_id, fields["name"])
        dish = Dish(restaurant_id=restaurant_id, **fields)
        self._dishes.add(dish)
        self._dishes.commit()
        return dish

    def update_dish(self, dish_id: int, changes: dict[str, Any]) -> Dish:
        dish = self._dish(dish_id)
        if "name" in changes:
            self._ensure_dish_name_free(dish.restaurant_id, changes["name"], exclude_id=dish_id)
        for field, value in changes.items():
            setattr(dish, field, value)
        self._dishes.commit()
        return dish

    def delete_dish(self, dish_id: int) -> None:
        # Past order items keep their name and price snapshot; dish_id becomes NULL.
        self._dishes.delete(self._dish(dish_id))
        self._dishes.commit()

    # ---- helpers

    def _cuisine(self, cuisine_id: int) -> Cuisine:
        cuisine = self._cuisines.get(cuisine_id)
        if cuisine is None:
            raise NotFoundError("Cuisine not found.", "CUISINE_NOT_FOUND")
        return cuisine

    def _dish(self, dish_id: int) -> Dish:
        dish = self._dishes.get(dish_id)
        if dish is None:
            raise NotFoundError("Dish not found.", "DISH_NOT_FOUND")
        return dish

    def _cuisines_by_ids(self, cuisine_ids: list[int]) -> list[Cuisine]:
        cuisines = self._cuisines.get_many(cuisine_ids)
        if len(cuisines) != len(set(cuisine_ids)):
            raise NotFoundError(
                "Some cuisines don't exist.", "CUISINE_NOT_FOUND", field="cuisine_ids"
            )
        return cuisines

    def _ensure_cuisine_name_free(self, name: str, exclude_id: int | None = None) -> None:
        if self._cuisines.name_taken(name, exclude_id):
            raise ConflictError("A cuisine with this name exists.", "CUISINE_EXISTS", field="name")

    def _ensure_restaurant_name_free(self, name: str, exclude_id: int | None = None) -> None:
        if self._restaurants.name_taken(name, exclude_id):
            raise ConflictError(
                "A restaurant with this name exists.", "RESTAURANT_EXISTS", field="name"
            )

    def _ensure_dish_name_free(
        self, restaurant_id: int, name: str, exclude_id: int | None = None
    ) -> None:
        if self._dishes.name_taken(restaurant_id, name, exclude_id):
            raise ConflictError(
                "This menu already has a dish with this name.", "DISH_EXISTS", field="name"
            )
