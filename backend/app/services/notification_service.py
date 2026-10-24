from dataclasses import dataclass

from ..domain.errors import NotFoundError
from ..models import Notification
from ..repositories import NotificationRepository

INBOX_SIZE = 20


@dataclass(frozen=True)
class Inbox:
    items: list[Notification]
    unread_count: int


class NotificationService:
    """The user's in-app inbox. Notifications are written by observers; this
    service only reads them and marks them read."""

    def __init__(self, notifications: NotificationRepository) -> None:
        self._notifications = notifications

    def inbox(self, user_id: int) -> Inbox:
        return Inbox(
            items=self._notifications.latest_for_user(user_id, INBOX_SIZE),
            unread_count=self._notifications.unread_count(user_id),
        )

    def mark_read(self, notification_id: int, user_id: int) -> Notification:
        notification = self._notifications.get_for_user(notification_id, user_id)
        if notification is None:
            raise NotFoundError("Notification not found.", "NOTIFICATION_NOT_FOUND")
        notification.is_read = True
        self._notifications.commit()
        return notification

    def mark_all_read(self, user_id: int) -> None:
        self._notifications.mark_all_read(user_id)
        self._notifications.commit()
