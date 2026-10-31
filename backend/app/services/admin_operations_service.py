from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

from ..domain.errors import ConflictError
from ..models import LoyaltySettings, NotificationType, Order, User, UserRole
from ..models.base import utcnow
from ..repositories import (
    LoyaltyRepository,
    NotificationRepository,
    OrderRepository,
    PageResult,
    UserRepository,
)


@dataclass(frozen=True)
class CourierSummary:
    courier: User
    active_order_ids: list[int]
    delivered_today: int


@dataclass(frozen=True)
class OrderFilters:
    status: str | None = None
    restaurant_id: int | None = None
    # Inclusive calendar days, interpreted in UTC.
    date_from: date | None = None
    date_to: date | None = None

    def created_range(self) -> tuple[datetime | None, datetime | None]:
        start = datetime.combine(self.date_from, time.min, UTC) if self.date_from else None
        end = (
            datetime.combine(self.date_to + timedelta(days=1), time.min, UTC)
            if self.date_to
            else None
        )
        return start, end


class AdminOperationsService:
    """Day-to-day admin work: courier accounts, the order board, loyalty
    settings and promo messages. Order status changes and cancellation reuse
    `OrderService` / the cancel command, so the same State rules apply to admins."""

    def __init__(
        self,
        users: UserRepository,
        orders: OrderRepository,
        loyalty: LoyaltyRepository,
        notifications: NotificationRepository,
        clock: Callable[[], datetime] = utcnow,
    ) -> None:
        self._users = users
        self._orders = orders
        self._loyalty = loyalty
        self._notifications = notifications
        self._clock = clock

    # ---- couriers

    def couriers(self) -> list[CourierSummary]:
        couriers = self._users.list_by_role(UserRole.COURIER)
        ids = [c.id for c in couriers]
        active = self._orders.active_order_ids_by_courier(ids)
        start_of_day = datetime.combine(self._clock().date(), time.min, UTC)
        delivered = self._orders.delivered_count_by_courier(ids, since=start_of_day)
        return [CourierSummary(c, active.get(c.id, []), delivered.get(c.id, 0)) for c in couriers]

    def create_courier(self, name: str, email: str, phone: str | None, password: str) -> User:
        if self._users.get_by_email(email) is not None:
            raise ConflictError(
                "An account with this email already exists.", "EMAIL_TAKEN", field="email"
            )
        courier = User(email=email, name=name, phone=phone, role=UserRole.COURIER)
        courier.set_password(password)
        self._users.add(courier)
        self._users.commit()
        return courier

    # ---- orders

    def orders(self, filters: OrderFilters, page: int, per_page: int) -> PageResult[Order]:
        created_from, created_to = filters.created_range()
        return self._orders.admin_page(
            status=filters.status,
            restaurant_id=filters.restaurant_id,
            created_from=created_from,
            created_to=created_to,
            page=page,
            per_page=per_page,
        )

    # ---- loyalty settings

    def loyalty_settings(self) -> LoyaltySettings:
        return self._loyalty.get_settings()

    def update_loyalty_settings(self, values: dict[str, Any]) -> LoyaltySettings:
        """Takes effect immediately for new quotes, deliveries and premium purchases;
        past points and orders stay as they were."""
        settings = self._loyalty.get_settings()
        for field, value in values.items():
            setattr(settings, field, value)
        self._loyalty.commit()
        return settings

    # ---- promotions

    def send_promotion(self, message: str) -> int:
        """In-app promo for every customer; returns how many received it."""
        customer_ids = self._users.ids_by_role(UserRole.CUSTOMER)
        self._notifications.notify_many(customer_ids, NotificationType.PROMO, message)
        self._notifications.commit()
        return len(customer_ids)
