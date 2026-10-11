from dataclasses import dataclass

from sqlalchemy import ColumnElement, Select, false, func, or_, select
from sqlalchemy.orm import selectinload

from ..domain.catalog.queries import RestaurantQuery, RestaurantSort
from ..domain.catalog.rules import CATALOG_TRAVEL_MINUTES, price_level_range
from ..models import Cuisine, Dish, Restaurant, Review, restaurant_cuisines
from .base import PageResult, SqlAlchemyRepository


@dataclass(frozen=True)
class RestaurantStats:
    """A restaurant plus aggregates computed in the same query."""

    restaurant: Restaurant
    rating: float | None
    review_count: int
    avg_dish_price: float | None


@dataclass(frozen=True)
class CuisineWithCount:
    cuisine: Cuisine
    restaurant_count: int


# Aggregates joined into restaurant queries: rating from reviews, price level
# basis from the average price of dishes currently on the menu.
_RATINGS = (
    select(
        Review.restaurant_id,
        func.avg(Review.rating).label("rating"),
        func.count(Review.id).label("review_count"),
    )
    .group_by(Review.restaurant_id)
    .subquery("ratings")
)
_PRICES = (
    select(Dish.restaurant_id, func.avg(Dish.price).label("avg_price"))
    .where(Dish.is_available.is_(True))
    .group_by(Dish.restaurant_id)
    .subquery("prices")
)


class RestaurantRepository(SqlAlchemyRepository):
    def _with_stats(self) -> Select:
        return (
            select(
                Restaurant,
                _RATINGS.c.rating,
                func.coalesce(_RATINGS.c.review_count, 0),
                _PRICES.c.avg_price,
            )
            .outerjoin(_RATINGS, _RATINGS.c.restaurant_id == Restaurant.id)
            .outerjoin(_PRICES, _PRICES.c.restaurant_id == Restaurant.id)
            .options(selectinload(Restaurant.cuisines))
        )

    @staticmethod
    def _to_stats(row: tuple) -> RestaurantStats:
        restaurant, rating, review_count, avg_price = row
        return RestaurantStats(
            restaurant=restaurant,
            rating=float(rating) if rating is not None else None,
            review_count=int(review_count),
            avg_dish_price=float(avg_price) if avg_price is not None else None,
        )

    def _price_level_condition(self, levels: list[int]) -> ColumnElement[bool]:
        conditions = []
        for level in levels:
            lower, upper = price_level_range(level)
            parts = []
            if lower is not None:
                parts.append(_PRICES.c.avg_price >= lower)
            if upper is not None:
                parts.append(_PRICES.c.avg_price < upper)
            conditions.append(parts[0] if len(parts) == 1 else parts[0] & parts[1])
        return or_(*conditions) if conditions else false()

    def search(self, query: RestaurantQuery) -> PageResult[RestaurantStats]:
        stmt = self._with_stats().where(Restaurant.is_active.is_(True))

        if query.cuisine_ids:
            stmt = stmt.where(Restaurant.cuisines.any(Cuisine.id.in_(query.cuisine_ids)))
        if query.price_levels:
            stmt = stmt.where(self._price_level_condition(query.price_levels))
        if query.max_delivery_minutes is not None:
            slowest_ride = CATALOG_TRAVEL_MINUTES[1]
            stmt = stmt.where(
                Restaurant.avg_prep_minutes + slowest_ride <= query.max_delivery_minutes
            )
        if query.min_rating is not None:
            stmt = stmt.where(_RATINGS.c.rating >= query.min_rating)

        total = self._session.scalar(select(func.count()).select_from(stmt.subquery())) or 0

        order_by = {
            RestaurantSort.RATING: [
                _RATINGS.c.rating.desc().nulls_last(),
                func.coalesce(_RATINGS.c.review_count, 0).desc(),
            ],
            RestaurantSort.DELIVERY_TIME: [Restaurant.avg_prep_minutes.asc()],
            RestaurantSort.PRICE: [_PRICES.c.avg_price.asc().nulls_last()],
        }[query.sort]
        stmt = (
            stmt.order_by(*order_by, Restaurant.name)
            .offset((query.page - 1) * query.per_page)
            .limit(query.per_page)
        )
        items = [self._to_stats(row) for row in self._session.execute(stmt).all()]
        return PageResult(items=items, total=total, page=query.page, per_page=query.per_page)

    def get_active_with_stats(self, restaurant_id: int) -> RestaurantStats | None:
        stmt = self._with_stats().where(
            Restaurant.id == restaurant_id, Restaurant.is_active.is_(True)
        )
        row = self._session.execute(stmt).first()
        return self._to_stats(row.tuple()) if row else None

    def get_active(self, restaurant_id: int) -> Restaurant | None:
        return self._session.scalar(
            select(Restaurant).where(Restaurant.id == restaurant_id, Restaurant.is_active.is_(True))
        )

    def rating_breakdown(self, restaurant_id: int) -> dict[int, int]:
        rows = self._session.execute(
            select(Review.rating, func.count(Review.id))
            .where(Review.restaurant_id == restaurant_id)
            .group_by(Review.rating)
        ).all()
        return {int(rating): int(count) for rating, count in rows}


class DishRepository(SqlAlchemyRepository):
    def get_many_for_restaurant(self, restaurant_id: int, dish_ids: list[int]) -> list[Dish]:
        """Only dishes that belong to the restaurant; foreign ids are simply absent."""
        if not dish_ids:
            return []
        return list(
            self._session.scalars(
                select(Dish).where(Dish.restaurant_id == restaurant_id, Dish.id.in_(dish_ids))
            )
        )

    def list_for_restaurant(self, restaurant_id: int) -> list[Dish]:
        return list(
            self._session.scalars(
                select(Dish).where(Dish.restaurant_id == restaurant_id).order_by(Dish.id)
            )
        )


class CuisineRepository(SqlAlchemyRepository):
    def list_with_counts(self) -> list[CuisineWithCount]:
        active_count = func.count(Restaurant.id).filter(Restaurant.is_active.is_(True))
        rows = self._session.execute(
            select(Cuisine, active_count)
            .outerjoin(restaurant_cuisines, restaurant_cuisines.c.cuisine_id == Cuisine.id)
            .outerjoin(Restaurant, Restaurant.id == restaurant_cuisines.c.restaurant_id)
            .group_by(Cuisine.id)
            .order_by(Cuisine.name)
        ).all()
        return [CuisineWithCount(cuisine, int(count)) for cuisine, count in rows]
