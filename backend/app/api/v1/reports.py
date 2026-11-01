from flask import Blueprint, Response, jsonify

from ...container import get_services
from ...models import UserRole
from ...schemas.reports import ReportColumnOut, ReportInfoOut, ReportOut, ReportParams
from ..security import roles_required
from ..validation import parse_query

reports_bp = Blueprint("reports", __name__, url_prefix="/admin/reports")


@reports_bp.before_request
@roles_required(UserRole.ADMIN)
def require_admin() -> None:
    """Reports are admin-only."""


@reports_bp.get("")
def list_reports() -> Response:
    items = [
        ReportInfoOut(key=g.key, title=g.title).model_dump()
        for g in get_services().reports.available()
    ]
    return jsonify({"items": items})


@reports_bp.get("/<string:key>")
def get_report(key: str) -> Response:
    """`?format=csv` returns the same report as a CSV download."""
    params = parse_query(ReportParams)
    reports = get_services().reports
    if params.format == "csv":
        filename = f"{key}_{params.date_from}_{params.date_to}.csv"
        return Response(
            reports.generate_csv(key, params.date_from, params.date_to),
            mimetype="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    report = reports.generate(key, params.date_from, params.date_to)
    out = ReportOut(
        key=report.key,
        title=report.title,
        date_from=report.period.start,
        date_to=report.period.end,
        columns=[ReportColumnOut(key=c.key, label=c.label, kind=c.kind) for c in report.columns],
        rows=report.rows,
        totals=report.totals,
    )
    return jsonify(out.model_dump(mode="json"))
