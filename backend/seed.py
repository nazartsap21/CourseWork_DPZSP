"""Idempotent demo data loader: `python seed.py` (run after `flask db upgrade`).

Every entity is looked up by its natural key and inserted only when missing,
so re-running never duplicates rows and never overwrites admin edits.
Order history is created per customer only if that customer has no orders yet.
"""

from datetime import timedelta

from sqlalchemy import select

from app import create_app
from app.extensions import db
from app.models import (
    BonusReason,
    BonusTransaction,
    CardType,
    Cuisine,
    DeliveryMethod,
    Dish,
    Favorite,
    LoyaltyAccount,
    LoyaltySettings,
    Notification,
    NotificationType,
    Order,
    OrderItem,
    OrderStatus,
    OrderStatusHistory,
    Payment,
    PaymentMethod,
    PaymentPurpose,
    PaymentStatus,
    Restaurant,
    Review,
    User,
    UserRole,
)
from app.models.base import utcnow
from seed_data import (
    CUISINES,
    DEMO_PASSWORD,
    FAVORITES,
    ORDERS,
    PREMIUM_CARD,
    RESTAURANTS,
    USERS,
    OrderSeed,
)

KOPIYKY_PER_UAH = 100
# Historic fees for seeded orders; live fees come from the delivery strategies.
SEED_DELIVERY_FEES = {
    DeliveryMethod.STANDARD: 49 * KOPIYKY_PER_UAH,
    DeliveryMethod.EXPRESS: 89 * KOPIYKY_PER_UAH,
    DeliveryMethod.PICKUP: 0,
}
STATUS_LABELS = {
    OrderStatus.DELIVERED: "delivered",
    OrderStatus.CANCELLED: "cancelled",
}


def seed_settings() -> LoyaltySettings:
    settings = db.session.get(LoyaltySettings, LoyaltySettings.SINGLETON_ID)
    if settings is None:
        settings = LoyaltySettings(id=LoyaltySettings.SINGLETON_ID)
        db.session.add(settings)
        db.session.flush()
    return settings


def seed_cuisines() -> dict[str, Cuisine]:
    existing = {c.name: c for c in db.session.scalars(select(Cuisine))}
    for name in CUISINES:
        if name not in existing:
            existing[name] = Cuisine(name=name)
            db.session.add(existing[name])
    return existing


def seed_users() -> dict[str, User]:
    users: dict[str, User] = {}
    for data in USERS:
        user = db.session.scalar(select(User).where(User.email == data["email"]))
        if user is None:
            user = User(
                email=data["email"],
                name=data["name"],
                phone=data["phone"],
                role=UserRole(data["role"]),
            )
            user.set_password(DEMO_PASSWORD)
            db.session.add(user)
        if user.role == UserRole.CUSTOMER and user.loyalty_account is None:
            user.loyalty_account = LoyaltyAccount()
        users[data["email"]] = user
    db.session.flush()
    return users


def seed_restaurants(cuisines: dict[str, Cuisine]) -> dict[str, Restaurant]:
    restaurants: dict[str, Restaurant] = {}
    for data in RESTAURANTS:
        restaurant = db.session.scalar(select(Restaurant).where(Restaurant.name == data["name"]))
        if restaurant is None:
            restaurant = Restaurant(
                name=data["name"],
                description=data["description"],
                address=data["address"],
                lat=data["lat"],
                lng=data["lng"],
                avg_prep_minutes=data["avg_prep_minutes"],
                min_order_amount=data["min_order_uah"] * KOPIYKY_PER_UAH,
                cuisines=[cuisines[name] for name in data["cuisines"]],
            )
            db.session.add(restaurant)
        existing_dishes = {d.name for d in restaurant.dishes}
        for dish in data["dishes"]:
            if dish["name"] not in existing_dishes:
                restaurant.dishes.append(
                    Dish(
                        name=dish["name"],
                        description=dish["description"],
                        price=dish["price_uah"] * KOPIYKY_PER_UAH,
                        category=dish["category"],
                    )
                )
        restaurants[data["name"]] = restaurant
    db.session.flush()
    return restaurants


def seed_favorites(users: dict[str, User], restaurants: dict[str, Restaurant]) -> None:
    for email, names in FAVORITES.items():
        customer = users[email]
        current = {f.restaurant_id for f in customer.favorites}
        for name in names:
            if restaurants[name].id not in current:
                customer.favorites.append(Favorite(restaurant=restaurants[name]))


def seed_premium_card(users: dict[str, User], settings: LoyaltySettings) -> None:
    customer = users[PREMIUM_CARD["customer"]]
    account = customer.loyalty_account
    if account is None or account.card_type == CardType.PREMIUM:
        return
    bought_at = utcnow() - timedelta(days=PREMIUM_CARD["bought_days_ago"])
    account.card_type = CardType.PREMIUM
    account.premium_until = bought_at + timedelta(days=settings.premium_card_days)
    db.session.add(
        Payment(
            customer=customer,
            purpose=PaymentPurpose.PREMIUM_CARD,
            provider=PaymentMethod.MOCK,
            amount=settings.premium_card_price,
            status=PaymentStatus.PAID,
            created_at=bought_at,
            paid_at=bought_at,
        )
    )


def status_timeline(spec: OrderSeed, prep_minutes: int) -> list[tuple[OrderStatus, int]]:
    """(status, minutes after creation) for a plausible past order."""
    online = spec["payment_method"] != PaymentMethod.CASH
    steps: list[tuple[OrderStatus, int]] = [(OrderStatus.PENDING_PAYMENT, 0)] if online else []
    steps.append((OrderStatus.ACCEPTED, 1))
    if spec["status"] == OrderStatus.CANCELLED:
        return [*steps, (OrderStatus.CANCELLED, 6)]
    steps += [(OrderStatus.PREPARING, 3), (OrderStatus.READY_FOR_PICKUP, 3 + prep_minutes)]
    if spec["delivery_method"] == DeliveryMethod.PICKUP:
        return [*steps, (OrderStatus.DELIVERED, 15 + prep_minutes)]
    return [
        *steps,
        (OrderStatus.DELIVERING, 6 + prep_minutes),
        (OrderStatus.DELIVERED, 30 + prep_minutes),
    ]


def build_order(
    spec: OrderSeed,
    users: dict[str, User],
    restaurants: dict[str, Restaurant],
    settings: LoyaltySettings,
) -> Order:
    customer = users[spec["customer"]]
    restaurant = restaurants[spec["restaurant"]]
    dishes = {d.name: d for d in restaurant.dishes}
    method = DeliveryMethod(spec["delivery_method"])
    payment_method = PaymentMethod(spec["payment_method"])
    status = OrderStatus(spec["status"])
    created_at = utcnow() - timedelta(days=spec["days_ago"], hours=5)

    items = [
        OrderItem(dish=dishes[name], name=name, price=dishes[name].price, quantity=qty)
        for name, qty in spec["items"]
    ]
    subtotal = sum(item.price * item.quantity for item in items)
    delivery_fee = 0 if spec.get("free_delivery") else SEED_DELIVERY_FEES[method]
    points_used = spec.get("bonus_points_used", 0)
    discount = points_used * settings.point_value
    if spec.get("regular_discount"):
        discount += subtotal * settings.regular_customer_discount_percent // 100

    timeline = status_timeline(spec, restaurant.avg_prep_minutes)
    history_at = {s: created_at + timedelta(minutes=m) for s, m in timeline}
    delivered = status == OrderStatus.DELIVERED
    with_courier = delivered and method != DeliveryMethod.PICKUP

    order = Order(
        customer=customer,
        restaurant=restaurant,
        courier=users[spec["courier"]] if with_courier else None,
        status=status,
        delivery_method=method,
        delivery_address=spec.get("address"),
        delivery_lat=spec.get("lat"),
        delivery_lng=spec.get("lng"),
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        discount=discount,
        bonus_points_used=points_used,
        total=subtotal + delivery_fee - discount,
        payment_method=payment_method,
        payment_status=PaymentStatus.PAID if delivered else PaymentStatus.REFUNDED,
        picked_up_at=history_at.get(OrderStatus.DELIVERING),
        estimated_delivery_minutes=restaurant.avg_prep_minutes + 25 if with_courier else None,
        created_at=created_at,
        updated_at=history_at[status],
        items=items,
        status_history=[
            OrderStatusHistory(
                status=s,
                changed_at=at,
                changed_by=users[spec["courier"]]
                if with_courier and s in (OrderStatus.DELIVERING, OrderStatus.DELIVERED)
                else None,
            )
            for s, at in history_at.items()
        ],
    )
    # Cash is collected on delivery; online payments clear before acceptance.
    paid_on = (
        OrderStatus.DELIVERED if payment_method == PaymentMethod.CASH else OrderStatus.ACCEPTED
    )
    order.payments.append(
        Payment(
            customer=customer,
            purpose=PaymentPurpose.ORDER,
            provider=payment_method,
            amount=order.total,
            status=order.payment_status,
            created_at=created_at,
            paid_at=history_at.get(paid_on),
        )
    )
    if "review" in spec:
        rating, text = spec["review"]
        order.review = Review(
            restaurant=restaurant,
            customer=customer,
            rating=rating,
            text=text,
            created_at=history_at[status] + timedelta(hours=1),
        )
    return order


def apply_loyalty(order: Order, settings: LoyaltySettings) -> None:
    account = order.customer.loyalty_account
    assert account is not None
    finished_at = order.updated_at
    if order.bonus_points_used:
        account.points_balance -= order.bonus_points_used
        account.transactions.append(
            BonusTransaction(
                order=order,
                delta=-order.bonus_points_used,
                reason=BonusReason.ORDER_REDEMPTION,
                created_at=order.created_at,
            )
        )
    if order.status != OrderStatus.DELIVERED:
        if order.bonus_points_used:
            account.points_balance += order.bonus_points_used
            account.transactions.append(
                BonusTransaction(
                    order=order,
                    delta=order.bonus_points_used,
                    reason=BonusReason.REDEMPTION_REFUND,
                    created_at=finished_at,
                )
            )
        return
    earned = order.total // (100 * KOPIYKY_PER_UAH) * settings.points_per_100_uah
    account.completed_orders_count += 1
    if earned:
        account.points_balance += earned
        account.transactions.append(
            BonusTransaction(
                order=order,
                delta=earned,
                reason=BonusReason.ORDER_ACCRUAL,
                created_at=finished_at,
            )
        )


def notify(order: Order, is_read: bool) -> None:
    label = STATUS_LABELS[order.status]
    order.customer.notifications.append(
        Notification(
            type=NotificationType.ORDER_STATUS,
            message=f"Order #{order.id} from {order.restaurant.name} {label}.",
            order=order,
            is_read=is_read,
            created_at=order.updated_at,
        )
    )


def seed_order_history(
    users: dict[str, User], restaurants: dict[str, Restaurant], settings: LoyaltySettings
) -> int:
    has_orders = {
        email: db.session.scalar(select(Order.id).where(Order.customer_id == user.id).limit(1))
        is not None
        for email, user in users.items()
    }
    specs = sorted(
        (s for s in ORDERS if not has_orders[s["customer"]]), key=lambda s: -s["days_ago"]
    )
    for index, spec in enumerate(specs):
        order = build_order(spec, users, restaurants, settings)
        db.session.add(order)
        db.session.flush()
        apply_loyalty(order, settings)
        latest_for_customer = all(s["customer"] != spec["customer"] for s in specs[index + 1 :])
        notify(order, is_read=not latest_for_customer)
    return len(specs)


def run() -> None:
    settings = seed_settings()
    cuisines = seed_cuisines()
    users = seed_users()
    restaurants = seed_restaurants(cuisines)
    seed_favorites(users, restaurants)
    seed_premium_card(users, settings)
    created_orders = seed_order_history(users, restaurants, settings)
    db.session.commit()
    print(
        f"Seed complete: {len(users)} users, {len(restaurants)} restaurants, "
        f"{len(cuisines)} cuisines, {created_orders} new orders."
    )


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        run()
