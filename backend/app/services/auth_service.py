from dataclasses import dataclass

from ..domain.errors import (
    AuthenticationError,
    BusinessRuleError,
    ConflictError,
    NotFoundError,
)
from ..models import LoyaltyAccount, User, UserRole
from ..repositories import UserRepository


@dataclass(frozen=True)
class RegistrationData:
    email: str
    password: str
    name: str
    phone: str | None = None


class AuthService:
    """Registration, credential checks and profile lookup.

    Token issuing stays in the API layer: JWTs are an HTTP transport concern,
    and keeping them out lets this service be reused from CLI or tests.
    """

    def __init__(self, users: UserRepository) -> None:
        self._users = users

    def register_customer(self, data: RegistrationData) -> User:
        # Public sign-up always creates customers; couriers are created by admin.
        if self._users.get_by_email(data.email) is not None:
            raise ConflictError("An account with this email already exists.", "EMAIL_TAKEN")
        user = User(email=data.email, name=data.name, phone=data.phone, role=UserRole.CUSTOMER)
        user.set_password(data.password)
        user.loyalty_account = LoyaltyAccount()
        self._users.add(user)
        self._users.commit()
        return user

    def authenticate(self, email: str, password: str) -> User:
        user = self._users.get_by_email(email)
        # Same error for unknown email and wrong password, so the response
        # does not reveal which emails are registered.
        if user is None or not user.check_password(password):
            raise AuthenticationError("Email or password is incorrect.", "INVALID_CREDENTIALS")
        return user

    def update_profile(self, user_id: int, name: str, phone: str | None) -> User:
        user = self.get_user(user_id)
        user.name = name
        user.phone = phone
        self._users.commit()
        return user

    def change_password(self, user_id: int, current_password: str, new_password: str) -> None:
        user = self.get_user(user_id)
        # A field error, not 401: the session is valid, only the typed password is wrong.
        if not user.check_password(current_password):
            raise BusinessRuleError(
                "The current password is incorrect.", "WRONG_PASSWORD", field="current_password"
            )
        user.set_password(new_password)
        self._users.commit()

    def get_user(self, user_id: int) -> User:
        user = self._users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found.", "USER_NOT_FOUND")
        return user
