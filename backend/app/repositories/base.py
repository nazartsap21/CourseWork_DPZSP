from dataclasses import dataclass
from math import ceil

from sqlalchemy.orm import Session, scoped_session


@dataclass(frozen=True)
class PageResult[T]:
    items: list[T]
    total: int
    page: int
    per_page: int

    @property
    def pages(self) -> int:
        return ceil(self.total / self.per_page) if self.per_page else 0


class SqlAlchemyRepository:
    """Pure Fabrication: owns all query building so services stay persistence-agnostic.

    Receives the session from the app factory instead of importing `db`,
    which keeps repositories swappable in tests.
    """

    def __init__(self, session: Session | scoped_session[Session]) -> None:
        self._session = session

    def add(self, entity: object) -> None:
        self._session.add(entity)

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()
