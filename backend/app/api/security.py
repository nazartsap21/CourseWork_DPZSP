from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from ..domain.errors import PermissionDeniedError
from ..models import UserRole

P = ParamSpec("P")
R = TypeVar("R")


def roles_required(*roles: UserRole) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Requires a valid JWT whose `role` claim is one of `roles`.

    The role is read from the token rather than the DB: roles change rarely and
    tokens are short-lived, so this saves a query on every protected request.
    """

    def decorator(view: Callable[P, R]) -> Callable[P, R]:
        @wraps(view)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            verify_jwt_in_request()
            if get_jwt().get("role") not in roles:
                raise PermissionDeniedError("You don't have access to this resource.")
            return view(*args, **kwargs)

        return wrapper

    return decorator


def current_user_id() -> int:
    return int(get_jwt_identity())
