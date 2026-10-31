"""Admin catalog payloads. Money fields are integer kopiyky."""

from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints

from .catalog import CuisineOut
from .common import PageParams

MAX_MONEY = 10_000_00  # 10 000 UAH


def _http_url(value: str | None) -> str | None:
    value = (value or "").strip() or None
    if value is not None and not value.startswith(("https://", "http://", "/")):
        raise ValueError("Use an http(s) link or a path under /public.")
    return value


Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)]
ImageUrl = Annotated[str | None, Field(default=None, max_length=500), AfterValidator(_http_url)]


class CuisineIn(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=64)]


class AdminCuisineOut(CuisineOut):
    restaurant_count: int


class RestaurantFields(BaseModel):
    name: Name
    description: ShortText = ""
    address: Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=255)]
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    avg_prep_minutes: int = Field(ge=5, le=180)
    min_order_amount: int = Field(ge=0, le=MAX_MONEY)
    image_url: ImageUrl = None
    is_active: bool = True
    cuisine_ids: list[Annotated[int, Field(ge=1)]] = Field(min_length=1, max_length=5)


class RestaurantPatch(BaseModel):
    """Partial update: only the fields that are sent change (e.g. just `is_active`)."""

    name: Name | None = None
    description: ShortText | None = None
    address: (
        Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=255)]
        | None
    ) = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    avg_prep_minutes: int | None = Field(default=None, ge=5, le=180)
    min_order_amount: int | None = Field(default=None, ge=0, le=MAX_MONEY)
    image_url: ImageUrl = None
    is_active: bool | None = None
    cuisine_ids: list[Annotated[int, Field(ge=1)]] | None = Field(
        default=None, min_length=1, max_length=5
    )


class AdminRestaurantListParams(PageParams):
    q: Annotated[str, StringConstraints(strip_whitespace=True, max_length=80)] = ""
    active: bool | None = None


class AdminRestaurantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    address: str
    lat: float
    lng: float
    avg_prep_minutes: int
    min_order_amount: int
    image_url: str | None
    is_active: bool
    cuisines: list[CuisineOut]


class AdminRestaurantRowOut(AdminRestaurantOut):
    dish_count: int


class DishFields(BaseModel):
    name: Name
    description: ShortText = ""
    price: int = Field(ge=1, le=MAX_MONEY)
    category: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=64)]
    is_available: bool = True
    image_url: ImageUrl = None


class DishPatch(BaseModel):
    name: Name | None = None
    description: ShortText | None = None
    price: int | None = Field(default=None, ge=1, le=MAX_MONEY)
    category: (
        Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=64)] | None
    ) = None
    is_available: bool | None = None
    image_url: ImageUrl = None
