from sqlalchemy.orm import Session, scoped_session


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
