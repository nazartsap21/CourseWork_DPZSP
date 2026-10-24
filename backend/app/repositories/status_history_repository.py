from ..models import OrderStatus, OrderStatusHistory
from .base import SqlAlchemyRepository


class StatusHistoryRepository(SqlAlchemyRepository):
    """Implements `StatusHistorySink` for `StatusHistoryObserver`."""

    def record_status(self, order_id: int, status: str, changed_by_id: int | None) -> None:
        self._session.add(
            OrderStatusHistory(
                order_id=order_id, status=OrderStatus(status), changed_by_id=changed_by_id
            )
        )
