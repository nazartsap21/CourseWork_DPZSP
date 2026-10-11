"""The single place where exceptions become HTTP responses.

Every error leaves the API as {"error": {"code", "message"[, "details"]}} so the
frontend can handle all failures with one code path.
"""

from typing import Any

from flask import Flask, Response, jsonify
from flask_jwt_extended import JWTManager
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

from ..domain.errors import (
    AuthenticationError,
    BusinessRuleError,
    ConflictError,
    DomainError,
    NotFoundError,
    PermissionDeniedError,
)

DOMAIN_STATUS: dict[type[DomainError], int] = {
    NotFoundError: 404,
    ConflictError: 409,
    BusinessRuleError: 422,
    AuthenticationError: 401,
    PermissionDeniedError: 403,
}


def error_response(
    status: int, code: str, message: str, details: list[dict[str, Any]] | None = None
) -> tuple[Response, int]:
    body: dict[str, Any] = {"code": code, "message": message}
    if details:
        body["details"] = details
    return jsonify({"error": body}), status


def _field_errors(exc: ValidationError) -> list[dict[str, Any]]:
    details = []
    for err in exc.errors(include_url=False):
        # Custom validators raise ValueError; show their text without pydantic's prefix.
        ctx_error = err.get("ctx", {}).get("error")
        message = str(ctx_error) if err["type"] == "value_error" and ctx_error else err["msg"]
        details.append({"field": ".".join(str(p) for p in err["loc"]), "message": message})
    return details


def register_error_handlers(app: Flask, jwt: JWTManager) -> None:
    @app.errorhandler(DomainError)
    def handle_domain_error(exc: DomainError) -> tuple[Response, int]:
        status = next((code for cls, code in DOMAIN_STATUS.items() if isinstance(exc, cls)), 400)
        return error_response(status, exc.code, exc.message)

    @app.errorhandler(ValidationError)
    def handle_validation_error(exc: ValidationError) -> tuple[Response, int]:
        return error_response(
            422, "VALIDATION_ERROR", "Some fields are invalid.", _field_errors(exc)
        )

    @app.errorhandler(HTTPException)
    def handle_http_error(exc: HTTPException) -> tuple[Response, int]:
        status = exc.code or 500
        code = (exc.name or "error").upper().replace(" ", "_")
        return error_response(status, code, exc.description or exc.name)

    @jwt.unauthorized_loader
    def missing_token(reason: str) -> tuple[Response, int]:
        return error_response(401, "UNAUTHORIZED", "Sign in to continue.")

    @jwt.invalid_token_loader
    def invalid_token(reason: str) -> tuple[Response, int]:
        return error_response(401, "INVALID_TOKEN", "Your session is invalid. Sign in again.")

    @jwt.expired_token_loader
    def expired_token(header: dict[str, Any], payload: dict[str, Any]) -> tuple[Response, int]:
        return error_response(401, "TOKEN_EXPIRED", "Your session has expired. Sign in again.")
