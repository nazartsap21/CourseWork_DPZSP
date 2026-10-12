"""Builder pattern for orders.

An order has a few required parts (restaurant, dishes, delivery method) and
several optional ones (address, note, payment method, bonus points). Building
it step by step keeps call sites readable and lets `build()` check that the
required parts are present before anything is priced or saved.

The builder produces an `OrderDraft`, a plain value object with no ORM or Flask
dependency. Persistence turns a draft into `Order`/`OrderItem` rows later.
"""

from dataclasses import dataclass

from ..delivery.geo import GeoPoint
from ..errors import BusinessRuleError


@dataclass(frozen=True)
class RestaurantSnapshot:
    """What ordering needs to know about a restaurant. `min_order_amount` is kopiyky."""

    id: int
    name: str
    is_active: bool
    location: GeoPoint
    prep_minutes: int
    min_order_amount: int


@dataclass(frozen=True)
class DishSnapshot:
    """A dish as it is on the menu right now. `price` is kopiyky."""

    id: int
    restaurant_id: int
    name: str
    price: int
    is_available: bool


@dataclass(frozen=True)
class DraftItem:
    dish: DishSnapshot
    quantity: int

    @property
    def line_total(self) -> int:
        return self.dish.price * self.quantity


@dataclass(frozen=True)
class DeliveryDetails:
    method: str
    destination: GeoPoint | None = None
    address: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class OrderDraft:
    customer_id: int | None
    restaurant: RestaurantSnapshot
    items: tuple[DraftItem, ...]
    delivery: DeliveryDetails
    payment_method: str | None = None
    requested_points: int = 0

    @property
    def subtotal(self) -> int:
        return sum(item.line_total for item in self.items)


class OrderBuildError(BusinessRuleError):
    code = "ORDER_INCOMPLETE"


class OrderBuilder:
    """Collects the parts of an order. Each step returns the builder so calls chain:

    OrderBuilder(customer_id).for_restaurant(r).add_item(d, 2).with_delivery(...).build()
    """

    def __init__(self, customer_id: int | None = None) -> None:
        self.customer_id = customer_id
        self._restaurant: RestaurantSnapshot | None = None
        self._quantities: dict[int, int] = {}
        self._dishes: dict[int, DishSnapshot] = {}
        self._delivery: DeliveryDetails | None = None
        self._payment_method: str | None = None
        self._requested_points = 0

    def for_restaurant(self, restaurant: RestaurantSnapshot) -> "OrderBuilder":
        self._restaurant = restaurant
        return self

    def add_item(self, dish: DishSnapshot, quantity: int) -> "OrderBuilder":
        if quantity < 1:
            raise OrderBuildError(f"Quantity of {dish.name} must be at least 1.", field="items")
        if self._restaurant is not None and dish.restaurant_id != self._restaurant.id:
            raise OrderBuildError(
                f"{dish.name} is from another restaurant.", "DISH_NOT_FOUND", field="items"
            )
        # Adding the same dish twice increases the quantity instead of duplicating the line.
        self._dishes[dish.id] = dish
        self._quantities[dish.id] = self._quantities.get(dish.id, 0) + quantity
        return self

    def with_delivery(
        self,
        method: str,
        destination: GeoPoint | None = None,
        address: str | None = None,
        note: str | None = None,
    ) -> "OrderBuilder":
        self._delivery = DeliveryDetails(method, destination, address, note)
        return self

    def with_payment(self, method: str) -> "OrderBuilder":
        self._payment_method = method
        return self

    def redeem_points(self, points: int) -> "OrderBuilder":
        self._requested_points = max(points, 0)
        return self

    def build(self) -> OrderDraft:
        if self._restaurant is None:
            raise OrderBuildError("Choose a restaurant.", field="restaurant_id")
        if not self._quantities:
            raise OrderBuildError("Add at least one dish.", field="items")
        if self._delivery is None:
            raise OrderBuildError("Choose a delivery method.", field="delivery_method")
        items = tuple(
            DraftItem(self._dishes[dish_id], quantity)
            for dish_id, quantity in self._quantities.items()
        )
        return OrderDraft(
            customer_id=self.customer_id,
            restaurant=self._restaurant,
            items=items,
            delivery=self._delivery,
            payment_method=self._payment_method,
            requested_points=self._requested_points,
        )
