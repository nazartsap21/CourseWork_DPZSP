"""Admin report payloads. Money values are integer kopiyky."""

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel


class ReportParams(BaseModel):
    # Inclusive calendar days; the order of dates is checked by `ReportPeriod`.
    date_from: date
    date_to: date
    format: Literal["json", "csv"] = "json"


class ReportInfoOut(BaseModel):
    key: str
    title: str


class ReportColumnOut(BaseModel):
    key: str
    label: str
    kind: Literal["text", "count", "money", "minutes", "percent"]


class ReportOut(BaseModel):
    key: str
    title: str
    date_from: date
    date_to: date
    columns: list[ReportColumnOut]
    rows: list[dict[str, Any]]
    totals: dict[str, Any] | None
