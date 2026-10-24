from flask import Blueprint, Response, jsonify
from flask_jwt_extended import jwt_required

from ...container import get_services
from ...schemas.notifications import InboxOut, NotificationOut
from ..security import current_user_id

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")


@notifications_bp.get("")
@jwt_required()
def inbox() -> Response:
    """Latest notifications and the unread count; the header polls this."""
    result = get_services().notifications.inbox(current_user_id())
    out = InboxOut(
        items=[NotificationOut.model_validate(n) for n in result.items],
        unread_count=result.unread_count,
    )
    return jsonify(out.model_dump(mode="json"))


@notifications_bp.patch("/<int:notification_id>/read")
@jwt_required()
def mark_read(notification_id: int) -> Response:
    notification = get_services().notifications.mark_read(notification_id, current_user_id())
    return jsonify(NotificationOut.model_validate(notification).model_dump(mode="json"))


@notifications_bp.post("/read-all")
@jwt_required()
def mark_all_read() -> tuple[str, int]:
    get_services().notifications.mark_all_read(current_user_id())
    return "", 204
