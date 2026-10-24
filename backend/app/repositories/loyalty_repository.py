from sqlalchemy import select

from ..models import LoyaltyAccount, LoyaltySettings
from .base import SqlAlchemyRepository


class LoyaltyRepository(SqlAlchemyRepository):
    def get_account(self, customer_id: int, for_update: bool = False) -> LoyaltyAccount | None:
        """`for_update` locks the row until commit, so two checkouts can't spend
        the same points at once (PostgreSQL; SQLite ignores the lock)."""
        stmt = select(LoyaltyAccount).where(LoyaltyAccount.customer_id == customer_id)
        if for_update:
            stmt = stmt.with_for_update()
        return self._session.scalar(stmt)

    def get_settings(self) -> LoyaltySettings:
        """The single settings row; created with model defaults if the seed hasn't run."""
        settings = self._session.get(LoyaltySettings, LoyaltySettings.SINGLETON_ID)
        if settings is None:
            settings = LoyaltySettings(id=LoyaltySettings.SINGLETON_ID)
            self._session.add(settings)
            self._session.flush()
        return settings
