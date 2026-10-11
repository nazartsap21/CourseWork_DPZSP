from sqlalchemy import select

from ..models import User
from .base import SqlAlchemyRepository


class UserRepository(SqlAlchemyRepository):
    def get_by_id(self, user_id: int) -> User | None:
        return self._session.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self._session.scalar(select(User).where(User.email == email))
