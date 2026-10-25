from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from ..models import Review
from .base import PageResult, SqlAlchemyRepository


class ReviewRepository(SqlAlchemyRepository):
    def page_for_restaurant(
        self, restaurant_id: int, page: int, per_page: int
    ) -> PageResult[Review]:
        """Newest reviews first, with their authors."""
        total = (
            self._session.scalar(
                select(func.count(Review.id)).where(Review.restaurant_id == restaurant_id)
            )
            or 0
        )
        items = list(
            self._session.scalars(
                select(Review)
                .where(Review.restaurant_id == restaurant_id)
                .options(selectinload(Review.customer))
                .order_by(Review.created_at.desc(), Review.id.desc())
                .offset((page - 1) * per_page)
                .limit(per_page)
            )
        )
        return PageResult(items=items, total=total, page=page, per_page=per_page)

    def exists_for_order(self, order_id: int) -> bool:
        return (
            self._session.scalar(select(Review.id).where(Review.order_id == order_id)) is not None
        )
