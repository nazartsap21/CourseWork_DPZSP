from sqlalchemy import select

from ..models import User
from .base import SqlAlchemyRepository


class UserRepository(SqlAlchemyRepository):
    def get_by_id(self, user_id: int) -> User | None:
        return self._session.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self._session.scalar(select(User).where(User.email == email))

    def list_by_role(self, role: str) -> list[User]:
        return list(
            self._session.scalars(select(User).where(User.role == role).order_by(User.name))
        )

    def ids_by_role(self, role: str) -> list[int]:
        return list(self._session.scalars(select(User.id).where(User.role == role)))
