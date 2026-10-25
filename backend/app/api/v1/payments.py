from flask import Blueprint, Response, jsonify

from ...container import get_services
from ...models import UserRole
from ...schemas.orders import OrderOut, PaymentConfirmedOut, PaymentConfirmIn
from ..security import current_user_id, roles_required
from ..validation import parse_body

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")


@payments_bp.post("/confirm")
@roles_required(UserRole.CUSTOMER)
def confirm_payment() -> Response:
    """Called from the payment success page with the provider's session id.
    The backend asks the provider itself; the redirect alone proves nothing.
    Works for order payments and for the premium card."""
    body = parse_body(PaymentConfirmIn)
    result = get_services().payments.confirm(body.session_id, current_user_id())
    out = PaymentConfirmedOut(
        purpose=result.purpose,
        order=OrderOut.model_validate(result.order) if result.order else None,
        premium_until=result.premium_until,
    )
    return jsonify(out.model_dump(mode="json"))
