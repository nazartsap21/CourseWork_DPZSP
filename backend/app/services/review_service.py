from sqlalchemy.exc import IntegrityError

from ..domain.errors import BusinessRuleError, ConflictError, NotFoundError
from ..models import Order, OrderStatus, Review
from ..repositories import OrderRepository, PageResult, RestaurantRepository, ReviewRepository


def can_review(order: Order, customer_id: int) -> bool:
    """Own delivered order without a review yet."""
    return (
        order.customer_id == customer_id
        and order.status == OrderStatus.DELIVERED
        and order.review is None
    )


class ReviewService:
    """Customer reviews: one per delivered order. The restaurant rating is the
    average of these, computed by the catalog queries, so nothing else to update."""

    def __init__(
        self,
        reviews: ReviewRepository,
        orders: OrderRepository,
        restaurants: RestaurantRepository,
    ) -> None:
        self._reviews = reviews
        self._orders = orders
        self._restaurants = restaurants

    def create(self, order_id: int, customer_id: int, rating: int, text: str) -> Review:
        order = self._orders.get_with_details(order_id)
        if order is None or order.customer_id != customer_id:
            raise NotFoundError("Order not found.", "ORDER_NOT_FOUND")
        if order.status != OrderStatus.DELIVERED:
            raise BusinessRuleError(
                "You can rate the order once it has been delivered.", "REVIEW_NOT_ALLOWED"
            )
        if self._reviews.exists_for_order(order.id):
            raise ConflictError("You've already reviewed this order.", "REVIEW_EXISTS")
        review = Review(
            order_id=order.id,
            restaurant_id=order.restaurant_id,
            customer_id=customer_id,
            rating=rating,
            text=text,
        )
        self._reviews.add(review)
        try:
            self._reviews.commit()
        except IntegrityError:
            # Two submits at once: the unique constraint on order_id lets only one through.
            self._reviews.rollback()
            raise ConflictError("You've already reviewed this order.", "REVIEW_EXISTS") from None
        return review

    def for_restaurant(self, restaurant_id: int, page: int, per_page: int) -> PageResult[Review]:
        restaurant = self._restaurants.get_by_id(restaurant_id)
        if restaurant is None or not restaurant.is_active:
            raise NotFoundError("Restaurant not found.", "RESTAURANT_NOT_FOUND")
        return self._reviews.page_for_restaurant(restaurant_id, page, per_page)
