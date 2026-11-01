"""The concrete reports. Each fills in collect / aggregate / format_rows of
`ReportGenerator`; the pipeline itself lives in the base class."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from .base import ReportColumn, ReportGenerator, ReportPeriod, sum_columns

# ---- raw records (filled by the data source; plain data, no ORM)


@dataclass(frozen=True)
class OrderRecord:
    restaurant: str
    status: str
    discount: int
    total: int


@dataclass(frozen=True)
class SoldItemRecord:
    restaurant: str
    dish: str
    quantity: int
    line_total: int
    order_id: int


@dataclass(frozen=True)
class DeliveryRecord:
    courier: str
    total: int
    created_at: datetime
    picked_up_at: datetime | None
    delivered_at: datetime | None
    estimated_minutes: int | None


class ReportDataSource(Protocol):
    """Where the reports read from; implemented by `ReportRepository`. Every
    method selects by the order's creation date within the period."""

    def orders_created(self, period: ReportPeriod) -> list[OrderRecord]: ...

    def items_delivered(self, period: ReportPeriod) -> list[SoldItemRecord]: ...

    def courier_deliveries(self, period: ReportPeriod) -> list[DeliveryRecord]: ...


# ---- sales by restaurant


@dataclass
class RestaurantSales:
    restaurant: str
    delivered: int = 0
    cancelled: int = 0
    revenue: int = 0
    discounts: int = 0


class SalesByRestaurantReport(ReportGenerator[OrderRecord, RestaurantSales]):
    key = "sales_by_restaurant"
    title = "Sales by restaurant"
    columns = [
        ReportColumn("restaurant", "Restaurant"),
        ReportColumn("delivered", "Delivered orders", "count"),
        ReportColumn("cancelled", "Cancelled", "count"),
        ReportColumn("revenue", "Revenue", "money"),
        ReportColumn("average_check", "Average check", "money"),
        ReportColumn("discounts", "Discounts given", "money"),
    ]

    def __init__(self, source: ReportDataSource) -> None:
        self._source = source

    def collect(self, period: ReportPeriod) -> Sequence[OrderRecord]:
        return self._source.orders_created(period)

    def aggregate(self, records: Sequence[OrderRecord]) -> list[RestaurantSales]:
        groups: dict[str, RestaurantSales] = {}
        for record in records:
            group = groups.setdefault(record.restaurant, RestaurantSales(record.restaurant))
            if record.status == "delivered":
                group.delivered += 1
                group.revenue += record.total
                group.discounts += record.discount
            elif record.status == "cancelled":
                group.cancelled += 1
        return sorted(groups.values(), key=lambda g: (-g.revenue, g.restaurant))

    def format_rows(self, groups: list[RestaurantSales]) -> list[dict[str, Any]]:
        return [
            {
                "restaurant": g.restaurant,
                "delivered": g.delivered,
                "cancelled": g.cancelled,
                "revenue": g.revenue,
                "average_check": g.revenue // g.delivered if g.delivered else 0,
                "discounts": g.discounts,
            }
            for g in groups
        ]

    def totals(self, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
        totals = sum_columns(rows, ["delivered", "cancelled", "revenue", "discounts"])
        totals["average_check"] = (
            totals["revenue"] // totals["delivered"] if totals["delivered"] else 0
        )
        return totals


# ---- popular dishes


@dataclass
class DishSales:
    restaurant: str
    dish: str
    portions: int = 0
    revenue: int = 0
    order_ids: set[int] = field(default_factory=set)


class PopularDishesReport(ReportGenerator[SoldItemRecord, DishSales]):
    key = "popular_dishes"
    title = "Popular dishes"
    columns = [
        ReportColumn("dish", "Dish"),
        ReportColumn("restaurant", "Restaurant"),
        ReportColumn("portions", "Portions", "count"),
        ReportColumn("orders", "Orders", "count"),
        ReportColumn("revenue", "Revenue", "money"),
    ]

    def __init__(self, source: ReportDataSource) -> None:
        self._source = source

    def collect(self, period: ReportPeriod) -> Sequence[SoldItemRecord]:
        return self._source.items_delivered(period)

    def aggregate(self, records: Sequence[SoldItemRecord]) -> list[DishSales]:
        groups: dict[tuple[str, str], DishSales] = {}
        for record in records:
            key = (record.restaurant, record.dish)
            group = groups.setdefault(key, DishSales(record.restaurant, record.dish))
            group.portions += record.quantity
            group.revenue += record.line_total
            group.order_ids.add(record.order_id)
        return sorted(groups.values(), key=lambda g: (-g.portions, -g.revenue, g.dish))

    def format_rows(self, groups: list[DishSales]) -> list[dict[str, Any]]:
        return [
            {
                "dish": g.dish,
                "restaurant": g.restaurant,
                "portions": g.portions,
                "orders": len(g.order_ids),
                "revenue": g.revenue,
            }
            for g in groups
        ]

    def totals(self, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
        return sum_columns(rows, ["portions", "revenue"])


# ---- courier performance


@dataclass
class CourierStats:
    courier: str
    deliveries: int = 0
    ride_minutes: list[float] = field(default_factory=list)
    on_time: int = 0
    delivered_value: int = 0


class CourierPerformanceReport(ReportGenerator[DeliveryRecord, CourierStats]):
    key = "courier_performance"
    title = "Courier performance"
    columns = [
        ReportColumn("courier", "Courier"),
        ReportColumn("deliveries", "Deliveries", "count"),
        ReportColumn("average_ride", "Average ride", "minutes"),
        ReportColumn("on_time", "On time", "percent"),
        ReportColumn("delivered_value", "Orders delivered", "money"),
    ]

    def __init__(self, source: ReportDataSource) -> None:
        self._source = source

    def collect(self, period: ReportPeriod) -> Sequence[DeliveryRecord]:
        return self._source.courier_deliveries(period)

    def aggregate(self, records: Sequence[DeliveryRecord]) -> list[CourierStats]:
        groups: dict[str, CourierStats] = {}
        for record in records:
            group = groups.setdefault(record.courier, CourierStats(record.courier))
            group.deliveries += 1
            group.delivered_value += record.total
            if record.picked_up_at and record.delivered_at:
                ride = record.delivered_at - record.picked_up_at
                group.ride_minutes.append(ride.total_seconds() / 60)
            # On time = delivered within the ETA promised at checkout.
            if record.delivered_at and record.estimated_minutes is not None:
                took = (record.delivered_at - record.created_at).total_seconds() / 60
                if took <= record.estimated_minutes:
                    group.on_time += 1
        return sorted(groups.values(), key=lambda g: (-g.deliveries, g.courier))

    def format_rows(self, groups: list[CourierStats]) -> list[dict[str, Any]]:
        rows = []
        for g in groups:
            rides = g.ride_minutes
            rows.append(
                {
                    "courier": g.courier,
                    "deliveries": g.deliveries,
                    "average_ride": round(sum(rides) / len(rides)) if rides else None,
                    "on_time": round(g.on_time * 100 / g.deliveries) if g.deliveries else None,
                    "delivered_value": g.delivered_value,
                }
            )
        return rows

    def totals(self, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
        return sum_columns(rows, ["deliveries", "delivered_value"])
