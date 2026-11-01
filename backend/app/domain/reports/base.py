"""Template Method pattern for admin reports.

Every report goes through the same pipeline, fixed in `ReportGenerator.generate`:

    collect(period) -> aggregate(records) -> format_rows(aggregated) -> totals(rows)

The period handling, the result shape and the CSV output are shared; each
concrete report only fills in the steps that differ (which records, how to
group them, which columns). A new report is one subclass.
"""

import csv
import io
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Literal

from ..errors import BusinessRuleError

MAX_PERIOD_DAYS = 366

ColumnKind = Literal["text", "count", "money", "minutes", "percent"]
CSV_UNITS: dict[ColumnKind, str] = {"money": "UAH", "minutes": "min", "percent": "%"}


@dataclass(frozen=True)
class ReportPeriod:
    """Inclusive calendar days, e.g. 1–31 October."""

    start: date
    end: date

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise BusinessRuleError(
                "The start date must not be after the end date.",
                "INVALID_PERIOD",
                field="date_from",
            )
        if (self.end - self.start).days >= MAX_PERIOD_DAYS:
            raise BusinessRuleError(
                "Pick a period of one year or less.", "PERIOD_TOO_LONG", field="date_from"
            )

    @property
    def end_exclusive(self) -> date:
        return self.end + timedelta(days=1)


@dataclass(frozen=True)
class ReportColumn:
    """`kind` tells the UI and CSV how to show values: money is kopiyky,
    minutes are whole minutes, percent is 0–100."""

    key: str
    label: str
    kind: ColumnKind = "text"


@dataclass(frozen=True)
class Report:
    key: str
    title: str
    period: ReportPeriod
    columns: list[ReportColumn]
    rows: list[dict[str, Any]]
    totals: dict[str, Any] | None = field(default=None)


class ReportGenerator[RecordT, GroupT](ABC):
    """Base class of every report. Subclasses implement the three steps and may
    override the `totals` hook; they never change the order of the steps."""

    key: str
    title: str
    columns: list[ReportColumn]

    def generate(self, period: ReportPeriod) -> Report:
        """The template method: the same steps, in the same order, for every report."""
        records = self.collect(period)
        groups = self.aggregate(records)
        rows = self.format_rows(groups)
        return Report(
            key=self.key,
            title=self.title,
            period=period,
            columns=self.columns,
            rows=rows,
            totals=self.totals(rows),
        )

    @abstractmethod
    def collect(self, period: ReportPeriod) -> Sequence[RecordT]:
        """Raw records for the period (from the data source)."""

    @abstractmethod
    def aggregate(self, records: Sequence[RecordT]) -> list[GroupT]:
        """Group and compute per group."""

    @abstractmethod
    def format_rows(self, groups: list[GroupT]) -> list[dict[str, Any]]:
        """One dict per table row, keyed by column `key`, in display order."""

    def totals(self, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Hook: a summary row; no totals unless a report adds them."""
        return None


def sum_columns(rows: list[dict[str, Any]], keys: Sequence[str]) -> dict[str, int]:
    return {key: sum(row[key] for row in rows) for key in keys}


def to_csv(report: Report) -> str:
    """Shared CSV output: a header row with units, money as UAH with two decimals, a totals row."""

    def cell(column: ReportColumn, value: Any) -> str:
        if value is None:
            return ""
        if column.kind == "money":
            return f"{value / 100:.2f}"
        return str(value)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            f"{c.label} ({CSV_UNITS[c.kind]})" if c.kind in CSV_UNITS else c.label
            for c in report.columns
        ]
    )
    for row in report.rows:
        writer.writerow([cell(c, row.get(c.key)) for c in report.columns])
    if report.totals:
        writer.writerow(
            [
                "Total" if i == 0 else cell(c, report.totals.get(c.key))
                for i, c in enumerate(report.columns)
            ]
        )
    return buffer.getvalue()
