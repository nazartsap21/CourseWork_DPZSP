from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from ..domain.errors import NotFoundError
from ..domain.pricing.loyalty import LoyaltyRules, LoyaltyStatus, loyalty_status
from ..models import BonusTransaction, LoyaltyAccount
from ..models.base import utcnow
from ..repositories import LoyaltyRepository, UserRepository
from .payment_service import PaymentService

RECENT_TRANSACTIONS = 20


def account_status(account: LoyaltyAccount, rules: LoyaltyRules, now: datetime) -> LoyaltyStatus:
    """Regular / premium / balance for an account at a moment in time."""
    premium_until = account.premium_until
    # SQLite returns naive datetimes; values are always stored in UTC.
    if premium_until is not None and premium_until.tzinfo is None:
        premium_until = premium_until.replace(tzinfo=UTC)
    return loyalty_status(
        rules,
        completed_orders=account.completed_orders_count,
        card_type=account.card_type.value,
        premium_until=premium_until,
        points_balance=account.points_balance,
        now=now,
    )


@dataclass(frozen=True)
class LoyaltySummary:
    """Everything the account page shows. Money values are kopiyky."""

    account: LoyaltyAccount
    status: LoyaltyStatus
    rules: LoyaltyRules
    premium_price: int
    premium_days: int
    transactions: list[BonusTransaction]


class LoyaltyService:
    """The customer's loyalty program: balance, card, progress, and buying the
    premium card. Points are earned by `LoyaltyObserver` and spent at checkout."""

    def __init__(
        self,
        loyalty: LoyaltyRepository,
        users: UserRepository,
        payments: PaymentService,
        clock: Callable[[], datetime] = utcnow,
    ) -> None:
        self._loyalty = loyalty
        self._users = users
        self._payments = payments
        self._clock = clock

    def summary(self, customer_id: int) -> LoyaltySummary:
        account = self._account(customer_id)
        rules = self._loyalty.rules()
        settings = self._loyalty.get_settings()
        return LoyaltySummary(
            account=account,
            status=account_status(account, rules, self._clock()),
            rules=rules,
            premium_price=settings.premium_card_price,
            premium_days=settings.premium_card_days,
            transactions=self._loyalty.recent_transactions(account.id, RECENT_TRANSACTIONS),
        )

    def buy_premium(self, customer_id: int, payment_method: str) -> str:
        """Starts the card payment and returns where to send the customer.
        Buying while a card is active extends it (see `LoyaltyAccount.extend_premium`)."""
        account = self._account(customer_id)
        user = self._users.get_by_id(customer_id)
        if user is None:
            raise NotFoundError("User not found.", "USER_NOT_FOUND")
        price = self._loyalty.get_settings().premium_card_price
        return self._payments.start_premium(account, user.email, payment_method, price)

    def _account(self, customer_id: int) -> LoyaltyAccount:
        account = self._loyalty.get_account(customer_id)
        if account is None:
            raise NotFoundError("Loyalty account not found.", "LOYALTY_ACCOUNT_NOT_FOUND")
        return account
