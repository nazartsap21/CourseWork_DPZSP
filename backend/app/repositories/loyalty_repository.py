from sqlalchemy import select

from ..models import LoyaltyAccount, LoyaltySettings
from .base import SqlAlchemyRepository


class LoyaltyRepository(SqlAlchemyRepository):
    def get_account(self, customer_id: int) -> LoyaltyAccount | None:
        return self._session.scalar(
            select(LoyaltyAccount).where(LoyaltyAccount.customer_id == customer_id)
        )

    def get_settings(self) -> LoyaltySettings:
        """The single settings row; created with model defaults if the seed hasn't run."""
        settings = self._session.get(LoyaltySettings, LoyaltySettings.SINGLETON_ID)
        if settings is None:
            settings = LoyaltySettings(id=LoyaltySettings.SINGLETON_ID)
            self._session.add(settings)
            self._session.flush()
        return settings
