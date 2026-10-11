from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Protocol


class MenuDish(Protocol):
    id: int
    category: str


@dataclass
class MenuSection[DishT: MenuDish]:
    category: str
    dishes: list[DishT] = field(default_factory=list)


def group_menu[DishT: MenuDish](dishes: Iterable[DishT]) -> list[MenuSection[DishT]]:
    """Groups dishes by category. Categories keep the order in which the
    restaurant added them (by dish id), so the kitchen controls the menu layout."""
    sections: dict[str, MenuSection[DishT]] = {}
    for dish in sorted(dishes, key=lambda d: d.id):
        sections.setdefault(dish.category, MenuSection(dish.category)).dishes.append(dish)
    return list(sections.values())
