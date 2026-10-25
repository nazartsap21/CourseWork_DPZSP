from sqlalchemy import delete, select

from ..models import Favorite
from .base import SqlAlchemyRepository


class FavoriteRepository(SqlAlchemyRepository):
    def restaurant_ids(self, customer_id: int) -> list[int]:
        return list(
            self._session.scalars(
                select(Favorite.restaurant_id)
                .where(Favorite.customer_id == customer_id)
                .order_by(Favorite.created_at.desc())
            )
        )

    def exists(self, customer_id: int, restaurant_id: int) -> bool:
        return (
            self._session.scalar(
                select(Favorite.id).where(
                    Favorite.customer_id == customer_id, Favorite.restaurant_id == restaurant_id
                )
            )
            is not None
        )

    def remove(self, customer_id: int, restaurant_id: int) -> None:
        self._session.execute(
            delete(Favorite).where(
                Favorite.customer_id == customer_id, Favorite.restaurant_id == restaurant_id
            )
        )
