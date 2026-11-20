import unittest
from unittest.mock import MagicMock, patch

from modules.inaproc.api.cli import build_parser, main
from modules.inaproc.api.scraper import ScrapeResult

SAMPLE = "11469/SJ-IND.8/E-TKDN/7/2025"

class CliParserTest(unittest.TestCase):
    def test_parse_login(self):
        args = build_parser().parse_args(["login"])
        self.assertEqual(args.command, "login")

    def test_parse_probe(self):
        args = build_parser().parse_args(["probe", "--nomor", SAMPLE])
        self.assertEqual(args.command, "probe")
        self.assertEqual(args.nomor, SAMPLE)

    def test_parse_collect(self):
        args = build_parser().parse_args(
            ["collect", "--nomor", SAMPLE, "--start", "1000", "--end", "1100"]
        )
        self.assertEqual(args.command, "collect")
        self.assertEqual(args.start, 1000)
        self.assertEqual(args.end, 1100)
        self.assertFalse(args.force)

    def test_collect_butuh_rentang(self):
        with self.assertRaises(SystemExit):
            build_parser().parse_args(["collect", "--nomor", SAMPLE])

    def test_parse_gateway_status(self):
        args = build_parser().parse_args(["gateway-status"])
        self.assertEqual(args.command, "gateway-status")

class CliDispatchTest(unittest.TestCase):
    def test_probe_mencetak_jumlah_baris(self):
        scraper = MagicMock()
        scraper.fetch.return_value = ScrapeResult(status="found", rows=[{"brand": "acer"}])
        with patch("modules.inaproc.api.cli.TkdnScraper", return_value=scraper), patch(
            "modules.inaproc.api.cli.print"
        ) as printer, patch("modules.inaproc.api.cli.load_env_file"):
            main(["probe", "--nomor", SAMPLE, "--session", "session.json"])
        self.assertEqual(scraper.fetch.call_count, 1)
        self.assertTrue(printer.called)

    def test_gateway_status_tanpa_token_tidak_memanggil_api(self):
        with patch.dict(
            "os.environ",
            {"INAPROC_API_TOKEN": "", "INAPROC_API_ENABLED": "true"},
            clear=False,
        ), patch("modules.inaproc.api.cli.load_env_file"), patch(
            "modules.inaproc.api.cli.print"
        ) as printer:
            main(["gateway-status"])
        output = " ".join(str(c.args[0]) for c in printer.call_args_list)
        self.assertIn("disabled", output)
        self.assertIn("produk", output)
        self.assertNotIn("ekatalog-v6", output)

if __name__ == "__main__":
    unittest.main()
