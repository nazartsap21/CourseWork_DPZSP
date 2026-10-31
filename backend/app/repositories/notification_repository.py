from sqlalchemy import func, select, update

from ..models import Notification, NotificationType
from .base import SqlAlchemyRepository


class NotificationRepository(SqlAlchemyRepository):
    """Implements `NotificationSink` for `NotificationObserver`, plus inbox queries."""

    def notify(self, user_id: int, type: str, message: str, order_id: int | None) -> None:
        self._session.add(
            Notification(
                user_id=user_id, type=NotificationType(type), message=message, order_id=order_id
            )
        )

    def latest_for_user(self, user_id: int, limit: int) -> list[Notification]:
        return list(
            self._session.scalars(
                select(Notification)
                .where(Notification.user_id == user_id)
                .order_by(Notification.created_at.desc(), Notification.id.desc())
                .limit(limit)
            )
        )

    def unread_count(self, user_id: int) -> int:
        return (
            self._session.scalar(
                select(func.count(Notification.id)).where(
                    Notification.user_id == user_id, Notification.is_read.is_(False)
                )
            )
            or 0
        )

    def get_for_user(self, notification_id: int, user_id: int) -> Notification | None:
        return self._session.scalar(
            select(Notification).where(
                Notification.id == notification_id, Notification.user_id == user_id
            )
        )

    def mark_all_read(self, user_id: int) -> None:
        self._session.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .values(is_read=True)
        )

    def notify_many(self, user_ids: list[int], type: str, message: str) -> None:
        """One notification per user, e.g. an admin promo to all customers."""
        self._session.add_all(
            Notification(user_id=user_id, type=NotificationType(type), message=message)
            for user_id in user_ids
        )
