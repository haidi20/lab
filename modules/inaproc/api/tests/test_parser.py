import unittest
from pathlib import Path

from modules.inaproc.api.parser import ParserError, parse_rows

FIXTURE = Path(__file__).parent / "fixtures" / "tkdn_table.html"


class ParseRowsTest(unittest.TestCase):
    def setUp(self):
        self.html = FIXTURE.read_text(encoding="utf-8")

    def test_parse_tabel(self):
        rows = parse_rows(self.html)
        self.assertEqual(len(rows), 2)
        first = rows[0]
        self.assertEqual(first["product_type"], "Monitor")
        self.assertEqual(first["brand"], "acer")
        self.assertEqual(first["type"], "V")
        self.assertEqual(first["description"], "23.8 Inchi")
        self.assertEqual(first["standard"], "-")
        self.assertAlmostEqual(first["value"], 33.39)

    def test_tabel_kosong(self):
        html = "<html><body><table><thead><tr><th>Jenis Produk</th></tr></thead><tbody></tbody></table></body></html>"
        self.assertEqual(parse_rows(html), [])

    def test_nilai_desimal(self):
        rows = parse_rows(self.html)
        self.assertAlmostEqual(rows[1]["value"], 41.2)

    def test_nilai_kosong_jadi_none(self):
        html = """
        <table><tbody><tr>
          <td>Monitor</td><td>acer</td><td>V</td><td>24 Inchi</td><td></td><td></td>
        </tr></tbody></table>
        """
        rows = parse_rows(html)
        self.assertIsNone(rows[0]["value"])
        self.assertIsNone(rows[0]["standard"])

    def test_baris_ganda(self):
        rows = parse_rows(self.html)
        self.assertEqual([r["brand"] for r in rows], ["acer", "Lenovo"])

    def test_markup_berubah(self):
        with self.assertRaises(ParserError):
            parse_rows("<html><body><div>no table here</div></body></html>")

    def test_tanpa_kolom_wajib(self):
        with self.assertRaises(ParserError):
            parse_rows("<table><tbody><tr><td>a</td><td>b</td></tr></tbody></table>")


if __name__ == "__main__":
    unittest.main()
