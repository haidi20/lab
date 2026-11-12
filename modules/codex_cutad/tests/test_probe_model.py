"""Tests untuk modules/codex_cutad/probe_model.py.

Dipakai sebelum switch model Codex: membuktikan gateway CutadAI benar-benar
menerima model target lewat `/v1/responses` (jalur Codex 0.167) sehingga
switch tidak berakhir `11128 Upstream error. Contact support if this
persists.` Tidak ada request jaringan di sini: `urllib` di-stub.
"""
import importlib
import io
import json
import unittest
import urllib.error

probe = importlib.import_module("modules.codex_cutad.probe_model")

CONFIG = """\
model = "tencent/hy4-preview"
model_provider = "cutad"

[model_providers.cutad-direct]
name = "CutadAI (direct)"
base_url = "https://ai.cutad.web.id/v1"
wire_api = "responses"
experimental_bearer_token = "cag_TESTTOKEN"

[model_providers.cutad]
base_url = "http://127.0.0.1:8787/v1"
"""


class TestKonfigurasi(unittest.TestCase):
    def test_token_dibaca_dari_config(self):
        self.assertEqual(probe.token_dari_config(CONFIG), "cag_TESTTOKEN")

    def test_token_tidak_ada(self):
        self.assertIsNone(probe.token_dari_config("[tui]\nx = 1\n"))

    def test_base_url_dari_provider_direct(self):
        self.assertEqual(
            probe.base_url_dari_config(CONFIG),
            "https://ai.cutad.web.id/v1/responses",
        )

    def test_base_url_fallback_tanpa_tabel(self):
        self.assertEqual(
            probe.base_url_dari_config("model = \"x\"\n"), probe.URL_DEFAULT
        )


class TestPayload(unittest.TestCase):
    def test_varian_minimal_tanpa_developer(self):
        isi = json.dumps(probe.varian("deepseek-v4-pro")["minimal"])
        self.assertNotIn("developer", isi)
        self.assertEqual(
            probe.varian("deepseek-v4-pro")["minimal"]["model"],
            "deepseek-v4-pro",
        )

    def test_varian_codex_ish_memakai_developer(self):
        isi = json.dumps(probe.varian("deepseek-v4-pro")["codex-ish"])
        self.assertIn("developer", isi)

    def test_ringkas_balasan_dari_sse_delta(self):
        sse = (
            'event: response.output_text.delta\n'
            'data: {"type":"response.output_text.delta","delta":"PONG"}\n\n'
        )
        self.assertEqual(probe.ringkas_balasan(sse), "PONG")

    def test_ringkas_balasan_error_json(self):
        teks = json.dumps(
            {"error": {"code": "11128", "message": "Upstream error."}}
        )
        self.assertTrue(probe.ringkas_balasan(teks).startswith("ERROR"))


class TestKirim(unittest.TestCase):
    def setUp(self):
        self._asli = probe.urllib.request.urlopen

    def tearDown(self):
        probe.urllib.request.urlopen = self._asli

    def _stub(self, fungsi):
        probe.urllib.request.urlopen = fungsi

    def test_200_dianggap_ok(self):
        class Resp(io.BytesIO):
            status = 200
            headers = {"Content-Type": "text/event-stream"}

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        body = b'data: {"type":"response.output_text.delta","delta":"PONG"}\n'
        self._stub(lambda req, timeout=None, context=None: Resp(body))
        hasil = probe.kirim({"model": "deepseek-v4-pro"}, "tok")
        self.assertTrue(hasil["ok"])
        self.assertEqual(hasil["status"], 200)
        self.assertIn("PONG", hasil["teks"])

    def test_11128_dilaporkan_sebagai_gagal(self):
        body = json.dumps(
            {"error": {"code": "11128", "message": "Upstream error."}}
        ).encode()

        def palsu(req, timeout=None, context=None):
            raise urllib.error.HTTPError(
                "https://x/v1/responses", 400, "Bad Request",
                {"Content-Encoding": ""}, io.BytesIO(body),
            )

        self._stub(palsu)
        hasil = probe.kirim({"model": "deepseek-v4-pro"}, "tok")
        self.assertFalse(hasil["ok"])
        self.assertEqual(hasil["status"], 400)
        self.assertEqual(hasil["kode"], "11128")

    def test_pilih_varian_mengambil_yang_pertama_ok(self):
        hasil = {
            "minimal": {"ok": False},
            "developer": {"ok": True},
            "codex-ish": {"ok": True},
        }
        self.assertEqual(probe.pilih_varian(hasil), "developer")

    def test_pilih_varian_semua_gagal(self):
        self.assertIsNone(
            probe.pilih_varian({"minimal": {"ok": False}})
        )


if __name__ == "__main__":
    unittest.main()
