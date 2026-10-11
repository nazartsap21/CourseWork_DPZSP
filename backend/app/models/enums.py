from enum import StrEnum


class UserRole(StrEnum):
    CUSTOMER = "customer"
    COURIER = "courier"
    ADMIN = "admin"


class OrderStatus(StrEnum):
    PENDING_PAYMENT = "pending_payment"
    ACCEPTED = "accepted"
    PREPARING = "preparing"
    READY_FOR_PICKUP = "ready_for_pickup"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class DeliveryMethod(StrEnum):
    STANDARD = "standard"
    EXPRESS = "express"
    PICKUP = "pickup"


class PaymentMethod(StrEnum):
    STRIPE = "stripe"
    CASH = "cash"
    MOCK = "mock"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentPurpose(StrEnum):
    ORDER = "order"
    PREMIUM_CARD = "premium_card"


class CardType(StrEnum):
    STANDARD = "standard"
    PREMIUM = "premium"


class BonusReason(StrEnum):
    ORDER_ACCRUAL = "order_accrual"
    ORDER_REDEMPTION = "order_redemption"
    REDEMPTION_REFUND = "redemption_refund"
    ADMIN_ADJUSTMENT = "admin_adjustment"


class NotificationType(StrEnum):
    ORDER_STATUS = "order_status"
    BONUS_POINTS = "bonus_points"
    PROMO = "promo"
