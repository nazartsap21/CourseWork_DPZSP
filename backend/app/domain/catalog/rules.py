"""Catalog-level estimates shown before the customer picks an address.

The exact fee and ETA for an order come from the delivery strategies at
checkout; here we only need something stable to filter and sort by.
"""

from dataclasses import dataclass

# Typical courier ride inside central Lviv, in minutes.
CATALOG_TRAVEL_MINUTES = (10, 20)

# Upper bounds (exclusive, in kopiyky) of the average dish price per level:
# level 1 is under 170 UAH, level 2 under 240 UAH, level 3 is everything above.
PRICE_LEVEL_UPPER_BOUNDS = (17_000, 24_000)
MAX_PRICE_LEVEL = len(PRICE_LEVEL_UPPER_BOUNDS) + 1


@dataclass(frozen=True)
class DeliveryWindow:
    min_minutes: int
    max_minutes: int


def catalog_delivery_window(avg_prep_minutes: int) -> DeliveryWindow:
    low, high = CATALOG_TRAVEL_MINUTES
    return DeliveryWindow(avg_prep_minutes + low, avg_prep_minutes + high)


def price_level(avg_dish_price: float | None) -> int | None:
    if avg_dish_price is None:
        return None
    for level, upper in enumerate(PRICE_LEVEL_UPPER_BOUNDS, start=1):
        if avg_dish_price < upper:
            return level
    return MAX_PRICE_LEVEL


def price_level_range(level: int) -> tuple[int | None, int | None]:
    """[lower, upper) average-price range in kopiyky for a level; None = unbounded."""
    bounds: list[int | None] = [None, *PRICE_LEVEL_UPPER_BOUNDS, None]
    return bounds[level - 1], bounds[level]
