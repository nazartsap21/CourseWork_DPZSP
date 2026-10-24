from sqlalchemy import select

from ..models import Payment
from .base import SqlAlchemyRepository


class PaymentRepository(SqlAlchemyRepository):
    def get_by_external_id(self, external_id: str) -> Payment | None:
        return self._session.scalar(select(Payment).where(Payment.external_id == external_id))
