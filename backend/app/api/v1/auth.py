from flask import Blueprint, Response, jsonify
from flask_jwt_extended import create_access_token, jwt_required

from ...container import get_services
from ...models import User
from ...schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserOut
from ...services.auth_service import RegistrationData
from ..security import current_user_id
from ..validation import parse_body

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _auth_response(user: User) -> AuthResponse:
    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role.value})
    return AuthResponse(access_token=token, user=UserOut.model_validate(user))


@auth_bp.post("/register")
def register() -> tuple[Response, int]:
    body = parse_body(RegisterRequest)
    user = get_services().auth.register_customer(
        RegistrationData(email=body.email, password=body.password, name=body.name, phone=body.phone)
    )
    return jsonify(_auth_response(user).model_dump(mode="json")), 201


@auth_bp.post("/login")
def login() -> Response:
    body = parse_body(LoginRequest)
    user = get_services().auth.authenticate(body.email, body.password)
    return jsonify(_auth_response(user).model_dump(mode="json"))


@auth_bp.get("/me")
@jwt_required()
def me() -> Response:
    user = get_services().auth.get_user(current_user_id())
    return jsonify(UserOut.model_validate(user).model_dump(mode="json"))
