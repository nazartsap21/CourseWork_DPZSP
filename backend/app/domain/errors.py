"""Domain exceptions. Each carries a stable machine-readable `code`; the API
layer maps the exception *category* to an HTTP status in one place
(app/api/errors.py), so the domain never deals with HTTP."""


class DomainError(Exception):
    code = "DOMAIN_ERROR"

    def __init__(self, message: str, code: str | None = None, field: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        # Optional request field the error is about, so forms can show it inline.
        self.field = field
        if code is not None:
            self.code = code


class NotFoundError(DomainError):
    code = "NOT_FOUND"


class ConflictError(DomainError):
    """The request clashes with current state (duplicate email, invalid status transition)."""

    code = "CONFLICT"


class BusinessRuleError(DomainError):
    """Input is well-formed but breaks a business rule (below minimum order, outside zone)."""

    code = "BUSINESS_RULE_VIOLATION"


class AuthenticationError(DomainError):
    code = "UNAUTHORIZED"


class ExternalServiceError(DomainError):
    """A third-party service (payment provider, routing API) failed."""

    code = "EXTERNAL_SERVICE_ERROR"


class PermissionDeniedError(DomainError):
    code = "FORBIDDEN"
