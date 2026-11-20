from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote


@dataclass(frozen=True)
class SptNumber:
    sequence: int
    unit: str
    doc_type: str
    month: int
    year: int

    @classmethod
    def parse(cls, text: str) -> "SptNumber":
        parts = (text or "").strip().split("/")
        if len(parts) != 5:
            raise ValueError(
                f"SPT number must have 5 parts separated by '/', got {len(parts)}"
            )
        sequence_raw, unit, doc_type, month_raw, year_raw = parts
        try:
            sequence = int(sequence_raw)
        except ValueError as exc:
            raise ValueError(f"SPT sequence must be numeric, got {sequence_raw!r}") from exc
        if sequence <= 0:
            raise ValueError("SPT sequence must be positive")
        try:
            month = int(month_raw)
        except ValueError as exc:
            raise ValueError(f"SPT month must be numeric, got {month_raw!r}") from exc
        if not 1 <= month <= 12:
            raise ValueError(f"SPT month must be 1-12, got {month}")
        if len(year_raw) != 4 or not year_raw.isdigit():
            raise ValueError(f"SPT year must be 4 digits, got {year_raw!r}")
        if not unit or not doc_type:
            raise ValueError("SPT unit and document type must not be empty")
        return cls(
            sequence=sequence,
            unit=unit,
            doc_type=doc_type,
            month=month,
            year=int(year_raw),
        )

    def with_sequence(self, sequence: int) -> "SptNumber":
        return SptNumber(
            sequence=sequence,
            unit=self.unit,
            doc_type=self.doc_type,
            month=self.month,
            year=self.year,
        )

    def __str__(self) -> str:
        return f"{self.sequence}/{self.unit}/{self.doc_type}/{self.month}/{self.year}"


def build_keyword(spt: SptNumber) -> str:
    return quote(str(spt), safe="")


def sequence_range(template: SptNumber, start: int, end: int) -> list[SptNumber]:
    if start > end:
        raise ValueError("start must be less than or equal to end")
    return [template.with_sequence(n) for n in range(start, end + 1)]
