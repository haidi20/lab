from __future__ import annotations

import csv
import io
import json
from typing import Any, Sequence

EXPORT_COLUMNS = (
    "number",
    "product_type",
    "brand",
    "type",
    "description",
    "standard",
    "value",
    "hs",
)

PRODUK_COLUMNS = (
    "kd_produk",
    "kode_penyedia",
    "nama_produk",
    "kategori",
    "brand",
    "harga",
    "satuan",
    "source_url",
)

PAKET_COLUMNS = (
    "kode_paket",
    "nama_paket",
    "tahun",
    "kode_klpd",
    "total_nilai",
    "source_url",
)

TRANSAKSI_COLUMNS = (
    "order_id",
    "kd_produk",
    "kode_penyedia",
    "nama_produk",
    "jumlah",
    "total",
    "tahun",
    "source_url",
)

CSV_BOM = "\ufeff"


def _cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def to_csv(
    rows: Sequence[dict[str, Any]],
    columns: Sequence[str] = EXPORT_COLUMNS,
) -> str:
    """Return UTF-8 CSV with BOM so Excel detects the encoding and commas."""
    buffer = io.StringIO()
    buffer.write(CSV_BOM)
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(columns)
    for row in rows:
        writer.writerow([_cell(row.get(column)) for column in columns])
    return buffer.getvalue()


def to_json(
    rows: Sequence[dict[str, Any]],
    columns: Sequence[str] = EXPORT_COLUMNS,
) -> str:
    payload = [
        {column: row.get(column) for column in columns}
        for row in rows
    ]
    return json.dumps(payload, ensure_ascii=False, indent=2)