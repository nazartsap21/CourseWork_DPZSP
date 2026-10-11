"""ORM entities. Importing this package registers every table on `db.metadata`,
which Alembic autogenerate and the app factory rely on."""

from .account import Favorite, Notification, Review
from .catalog import Cuisine, Dish, Restaurant, restaurant_cuisines
from .enums import (
    BonusReason,
    CardType,
    DeliveryMethod,
    NotificationType,
    OrderStatus,
    PaymentMethod,
    PaymentPurpose,
    PaymentStatus,
    UserRole,
)
from .loyalty import BonusTransaction, LoyaltyAccount, LoyaltySettings
from .order import Order, OrderItem, OrderStatusHistory
from .payment import Payment
from .user import User

__all__ = [
    "BonusReason",
    "BonusTransaction",
    "CardType",
    "Cuisine",
    "DeliveryMethod",
    "Dish",
    "Favorite",
    "LoyaltyAccount",
    "LoyaltySettings",
    "Notification",
    "NotificationType",
    "Order",
    "OrderItem",
    "OrderStatus",
    "OrderStatusHistory",
    "Payment",
    "PaymentMethod",
    "PaymentPurpose",
    "PaymentStatus",
    "Restaurant",
    "Review",
    "User",
    "UserRole",
    "restaurant_cuisines",
]
