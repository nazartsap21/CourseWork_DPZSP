from datetime import date

from ..domain.errors import NotFoundError
from ..domain.reports.base import Report, ReportGenerator, ReportPeriod, to_csv


class ReportService:
    """Looks up a report by key and runs it for a period. Knows nothing about
    individual reports: they are registered in the container."""

    def __init__(self, generators: list[ReportGenerator]) -> None:
        self._generators = {g.key: g for g in generators}

    def available(self) -> list[ReportGenerator]:
        return list(self._generators.values())

    def generate(self, key: str, date_from: date, date_to: date) -> Report:
        generator = self._generators.get(key)
        if generator is None:
            raise NotFoundError("There is no such report.", "REPORT_NOT_FOUND")
        return generator.generate(ReportPeriod(date_from, date_to))

    def generate_csv(self, key: str, date_from: date, date_to: date) -> str:
        return to_csv(self.generate(key, date_from, date_to))
