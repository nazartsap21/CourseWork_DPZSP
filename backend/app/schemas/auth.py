import re
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints

from ..models import UserRole

# Pragmatic check instead of the email-validator package: the address is
# confirmed by actually using it, this only catches obvious typos.
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_PATTERN = re.compile(r"^\+?[0-9 ()-]{7,20}$")


def _normalize_email(value: str) -> str:
    value = value.strip().lower()
    if not EMAIL_PATTERN.match(value):
        raise ValueError("Enter a valid email address.")
    return value


def _check_phone(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    if not PHONE_PATTERN.match(value.strip()):
        raise ValueError("Enter a valid phone number, e.g. +380671234567.")
    return value.strip()


Email = Annotated[str, Field(max_length=255), AfterValidator(_normalize_email)]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]
Phone = Annotated[str | None, AfterValidator(_check_phone)]


class RegisterRequest(BaseModel):
    email: Email
    password: str = Field(min_length=8, max_length=128)
    name: Name
    phone: Phone = None


class LoginRequest(BaseModel):
    email: Email
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    phone: str | None
    role: UserRole
    created_at: datetime


class AuthResponse(BaseModel):
    access_token: str
    user: UserOut
