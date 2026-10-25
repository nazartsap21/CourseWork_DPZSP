from sqlalchemy import select

from ..domain.pricing.loyalty import LoyaltyRules
from ..models import BonusTransaction, LoyaltyAccount, LoyaltySettings, Order
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

    def rules(self) -> LoyaltyRules:
        """The settings row as the domain's plain `LoyaltyRules`."""
        settings = self.get_settings()
        return LoyaltyRules(
            points_per_100_uah=settings.points_per_100_uah,
            point_value=settings.point_value,
            max_points_redemption_percent=settings.max_points_redemption_percent,
            regular_customer_threshold=settings.regular_customer_threshold,
            regular_customer_discount_percent=settings.regular_customer_discount_percent,
        )

    def record_completed_order(self, customer_id: int, order_id: int, points: int) -> int | None:
        """Implements `LoyaltyLedger` for `LoyaltyObserver`; returns the new balance."""
        account = self.get_account(customer_id, for_update=True)
        order = self._session.get(Order, order_id)
        if account is None or order is None:
            return None
        account.add_completed_order(points, order)
        return account.points_balance

    def recent_transactions(self, account_id: int, limit: int) -> list[BonusTransaction]:
        return list(
            self._session.scalars(
                select(BonusTransaction)
                .where(BonusTransaction.account_id == account_id)
                .order_by(BonusTransaction.created_at.desc(), BonusTransaction.id.desc())
                .limit(limit)
            )
        )
