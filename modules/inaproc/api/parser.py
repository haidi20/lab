from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

REQUIRED_HEADERS = (
    "jenis produk",
    "merek",
    "tipe",
    "uraian produk",
    "standard",
    "nilai",
)

HEADER_TO_FIELD = {
    "jenis produk": "product_type",
    "merek": "brand",
    "tipe": "type",
    "uraian produk": "description",
    "standard": "standard",
    "nilai": "value",
}


class ParserError(RuntimeError):
    """Raised when the rendered TKDN table cannot be understood."""


def _text(cell: Any) -> str | None:
    value = " ".join(cell.get_text(" ", strip=True).split())
    return value or None


def _to_float(raw: str | None) -> float | None:
    if raw is None:
        return None
    normalized = raw.replace(".", "", raw.count(".") > 1).replace(",", ".")
    try:
        return float(normalized)
    except ValueError:
        return None


def _find_header_row(table: Any) -> list[str] | None:
    for row in table.find_all("tr"):
        cells = row.find_all(["th", "td"])
        labels = [" ".join(c.get_text(" ", strip=True).split()).lower() for c in cells]
        if all(header in labels for header in REQUIRED_HEADERS):
            return labels
    return None


def _has_any_known_header(table: Any) -> bool:
    for row in table.find_all("tr"):
        labels = {
            " ".join(c.get_text(" ", strip=True).split()).lower()
            for c in row.find_all(["th", "td"])
        }
        if labels & set(HEADER_TO_FIELD):
            return True
    return False


def parse_rows(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if table is None:
        raise ParserError("TKDN table not found in rendered page")

    headers = _find_header_row(table)
    if headers is None:
        first_row = table.find("tr")
        first_cells = first_row.find_all(["td", "th"]) if first_row else []
        if len(first_cells) >= len(REQUIRED_HEADERS) and not _has_any_known_header(table):
            headers = list(REQUIRED_HEADERS)
        if _has_any_known_header(table):
            return []
        if headers is None:
            raise ParserError("TKDN table headers do not match the expected columns")

    index_by_field = {
        HEADER_TO_FIELD[label]: index
        for index, label in enumerate(headers)
        if label in HEADER_TO_FIELD
    }

    rows: list[dict[str, Any]] = []
    body = table.find("tbody") or table
    for row in body.find_all("tr"):
        cells = row.find_all("td")
        if not cells:
            continue
        if len(cells) < len(headers):
            continue
        record = {
            field: _text(cells[index]) if index < len(cells) else None
            for field, index in index_by_field.items()
        }
        if not any(record.values()):
            continue
        record["value"] = _to_float(record.get("value"))
        rows.append(record)
    return rows
