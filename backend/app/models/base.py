from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import Enum


def utcnow() -> datetime:
    return datetime.now(UTC)


def enum_column(enum_cls: type[StrEnum]) -> Enum:
    """Stores the enum *value* as VARCHAR rather than a native PG enum type.

    Adding a status later then needs no ALTER TYPE migration, and the DB holds
    the same lowercase strings the API exposes.
    """
    return Enum(
        enum_cls,
        native_enum=False,
        length=32,
        values_callable=lambda members: [member.value for member in members],
        validate_strings=True,
    )
