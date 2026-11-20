import csv
import io
import json
import unittest

from modules.inaproc.api.exporter import (
    PAKET_COLUMNS,
    PRODUK_COLUMNS,
    TRANSAKSI_COLUMNS,
    to_csv,
    to_json,
)

ROWS = [
    {
        "number": "n",
        "product_type": "Monitor",
        "brand": "acer",
        "type": "V",
        "description": "23.8 Inchi, IPS",
        "standard": None,
        "value": 33.39,
        "hs": None,
    }
]


class ExporterTest(unittest.TestCase):
    def test_header_csv(self):
        text = to_csv(ROWS)
        reader = csv.reader(io.StringIO(text.lstrip("\ufeff")))
        header = next(reader)
        self.assertEqual(
            header,
            ["number", "product_type", "brand", "type", "description", "standard", "value", "hs"],
        )

    def test_nilai_null(self):
        reader = csv.reader(io.StringIO(to_csv(ROWS).lstrip("\ufeff")))
        next(reader)
        row = next(reader)
        self.assertEqual(row[5], "")
        self.assertEqual(row[7], "")

    def test_escape_koma(self):
        reader = csv.reader(io.StringIO(to_csv(ROWS).lstrip("\ufeff")))
        next(reader)
        self.assertEqual(next(reader)[4], "23.8 Inchi, IPS")

    def test_json_struktur(self):
        data = json.loads(to_json(ROWS))
        self.assertEqual(data[0]["brand"], "acer")
        self.assertEqual(data[0]["value"], 33.39)

    def test_kolom_kustom_produk(self):
        rows = [{"kd_produk": "K1", "nama_produk": "Monitor", "harga": 1500000}]
        reader = csv.reader(io.StringIO(to_csv(rows, PRODUK_COLUMNS).lstrip("\ufeff")))
        header = next(reader)
        self.assertEqual(header, list(PRODUK_COLUMNS))
        self.assertEqual(next(reader)[0], "K1")

    def test_kolom_kustom_paket_json(self):
        rows = [{"kode_paket": "PK1", "nama_paket": "Paket Monitor", "tahun": 2026}]
        data = json.loads(to_json(rows, PAKET_COLUMNS))
        self.assertEqual(data[0]["kode_paket"], "PK1")
        self.assertEqual(set(data[0]), set(PAKET_COLUMNS))

    def test_kolom_kustom_transaksi_csv(self):
        rows = [{"order_id": "O1", "nama_produk": "Monitor", "total": 3000000}]
        reader = csv.reader(io.StringIO(to_csv(rows, TRANSAKSI_COLUMNS).lstrip("\ufeff")))
        next(reader)
        row = dict(zip(TRANSAKSI_COLUMNS, next(reader)))
        self.assertEqual(row["order_id"], "O1")
        self.assertEqual(row["total"], "3000000")


if __name__ == "__main__":
    unittest.main()
