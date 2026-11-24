"""Tests untuk modules/codex_cutad/shim.py.

Shim kecil di 127.0.0.1:8787 yang meneruskan `/v1/responses` Codex ke gateway
CutadAI sambil menulis ulang dua parameter yang DITOLAK gateway.

Bukti probe live (2026-11-14, key aktif `CODEX_CUTAD_API_KEY`):

    payload                                            hasil
    minimal / stream / store:false                     200
    reasoning {effort: low|none|high} + summary        200
    tools + tool_choice + parallel_tool_calls          200
    instructions + system message                      200
    prompt_cache_key / include / max_output_tokens     200
    role:"developer"                                   400 request_rejected
    previous_response_id                               400 unsupported_parameter

Jadi rewrite minimal = `developer -> system` + buang `previous_response_id`.
Tidak ada terjemahan Responses->Chat yang perlu dibuat.
"""
import importlib
import os
import unittest
from unittest import mock

shim = importlib.import_module("modules.codex_cutad.shim")


def pesan(teks, role):
    return {"type": "message", "role": role,
            "content": [{"type": "input_text", "text": teks}]}


class TestGantiDeveloper(unittest.TestCase):
    def test_developer_diubah_menjadi_system(self) -> None:
        payload = {"model": "deepseek-v4-pro",
                   "input": [pesan("instruksi", "developer"), pesan("halo", "user")]}
        baru, jumlah = shim.ganti_developer(payload)
        self.assertEqual(jumlah, 1)
        self.assertEqual(baru["input"][0]["role"], "system")
        self.assertEqual(baru["input"][1]["role"], "user")

    def test_role_lain_tidak_disentuh(self) -> None:
        payload = {"input": [pesan("a", "user"), pesan("b", "assistant"),
                             pesan("c", "system")]}
        baru, jumlah = shim.ganti_developer(payload)
        self.assertEqual(jumlah, 0)
        self.assertEqual([i["role"] for i in baru["input"]],
                         ["user", "assistant", "system"])

    def test_input_berupa_string_tidak_error(self) -> None:
        payload = {"input": "halo"}
        baru, jumlah = shim.ganti_developer(payload)
        self.assertEqual(jumlah, 0)
        self.assertEqual(baru["input"], "halo")

    def test_item_tanpa_role_tidak_error(self) -> None:
        payload = {"input": [{"type": "function_call_output", "call_id": "x",
                              "output": "ok"}]}
        baru, jumlah = shim.ganti_developer(payload)
        self.assertEqual(jumlah, 0)
        self.assertEqual(baru["input"][0]["type"], "function_call_output")


class TestBersihkanPayload(unittest.TestCase):
    def test_previous_response_id_dibuang(self) -> None:
        payload = {"model": "deepseek-v4-pro", "input": [pesan("hi", "user")],
                   "previous_response_id": "resp_abc"}
        baru, info = shim.bersihkan_payload(payload)
        self.assertNotIn("previous_response_id", baru)
        self.assertTrue(info["buang_prev"])

    def test_field_lain_dipertahankan(self) -> None:
        payload = {"model": "deepseek-v4-pro", "stream": True, "store": False,
                   "tools": [{"type": "function", "name": "shell"}],
                   "tool_choice": "auto", "parallel_tool_calls": False,
                   "reasoning": {"effort": "low"},
                   "prompt_cache_key": "k", "instructions": "x",
                   "input": [pesan("hi", "user")],
                   "previous_response_id": "resp_1"}
        baru, _ = shim.bersihkan_payload(payload)
        for kunci in ("model", "stream", "tools", "tool_choice",
                      "parallel_tool_calls", "reasoning", "prompt_cache_key",
                      "instructions", "input"):
            self.assertIn(kunci, baru, kunci)
        self.assertNotIn("store", baru)

    def test_idempoten(self) -> None:
        payload = {"model": "m", "input": [pesan("i", "developer")],
                   "previous_response_id": "r"}
        sekali, _ = shim.bersihkan_payload(payload)
        dua, info = shim.bersihkan_payload(sekali)
        self.assertEqual(sekali, dua)
        self.assertEqual(info["developer"], 0)
        self.assertFalse(info["buang_prev"])

    def test_payload_asli_tidak_dimutasi(self) -> None:
        payload = {"input": [pesan("i", "developer")],
                   "previous_response_id": "r"}
        shim.bersihkan_payload(payload)
        self.assertEqual(payload["input"][0]["role"], "developer")
        self.assertIn("previous_response_id", payload)


class TestUrlDanToken(unittest.TestCase):
    def test_url_responses(self) -> None:
        self.assertEqual(shim.url_target("/v1/responses"),
                         "https://ai.cutad.web.id/v1/responses")

    def test_url_tanpa_prefix_v1(self) -> None:
        self.assertEqual(shim.url_target("/responses"),
                         "https://ai.cutad.web.id/v1/responses")

    def test_url_models(self) -> None:
        self.assertEqual(shim.url_target("/v1/models"),
                         "https://ai.cutad.web.id/v1/models")

    def test_base_url_bisa_dioverride(self) -> None:
        self.assertEqual(
            shim.url_target("/v1/responses", base="http://contoh.test/v1"),
            "http://contoh.test/v1/responses")

    def test_token_prioritas_env_codex(self) -> None:
        env = {"CODEX_CUTAD_API_KEY": "kodex", "CUTAD_API_KEY": "lain"}
        with mock.patch.dict(os.environ, env, clear=False):
            self.assertEqual(shim.token_dari_env(), "kodex")

    def test_token_fallback_env_lama(self) -> None:
        env = {"CODEX_CUTAD_API_KEY": "", "CUTAD_API_KEY": "lain"}
        with mock.patch.dict(os.environ, env, clear=False):
            self.assertEqual(shim.token_dari_env(), "lain")

    def test_token_kosong_mengembalikan_none(self) -> None:
        env = {"CODEX_CUTAD_API_KEY": "", "CUTAD_API_KEY": ""}
        with mock.patch.dict(os.environ, env, clear=False):
            self.assertIsNone(shim.token_dari_env())


class TestLogAman(unittest.TestCase):
    def test_log_tidak_pernah_memuat_token(self) -> None:
        """Ringkasan log hanya memuat model + jumlah rewrite, bukan kredensial."""
        teks = shim.ringkas_log(
            "/v1/responses",
            {"model": "deepseek-v4-pro"},
            {"developer": 2, "buang_prev": True, "status": 200},
        )
        self.assertIn("deepseek-v4-pro", teks)
        self.assertIn("developer->system=2", teks)
        self.assertNotIn("cag_", teks)
        self.assertNotIn("Bearer", teks)


class TestHeaderUpstream(unittest.TestCase):
    def test_header_authorization_tidak_digandakan(self) -> None:
        hasil = shim.header_ke_upstream(
            {"content-type": "application/json", "authorization": "Bearer client"},
            token="server")
        self.assertEqual(hasil["Authorization"], "Bearer server")
        self.assertEqual(
            [k for k in hasil if k.lower() == "authorization"], ["Authorization"])

    def test_header_accept_dipertahankan(self) -> None:
        hasil = shim.header_ke_upstream({"accept": "text/event-stream"}, token="t")
        self.assertEqual(hasil["Accept"], "text/event-stream")

    def test_host_dan_content_length_dibuang(self) -> None:
        hasil = shim.header_ke_upstream(
            {"host": "127.0.0.1:8787", "content-length": "10",
             "connection": "keep-alive"}, token="t")
        for terlarang in ("Host", "Content-Length", "Connection"):
            self.assertNotIn(terlarang, hasil)


class TestRingkasReasoning(unittest.TestCase):
    """Gateway menolak `reasoning.summary` (400/3051), tetapi menerima effort."""

    def setUp(self) -> None:
        self.mod = importlib.import_module("modules.codex_cutad.shim")

    def test_summary_dibuang_effort_dipertahankan(self) -> None:
        baru, info = self.mod.bersihkan_payload(
            {"model": "m", "reasoning": {"effort": "none", "summary": "none"}})
        self.assertEqual(baru["reasoning"], {"effort": "none"})
        self.assertEqual(info["reasoning_summary"], 1)

    def test_reasoning_tanpa_summary_tidak_disentuh(self) -> None:
        asli = {"reasoning": {"effort": "high"}}
        baru, info = self.mod.bersihkan_payload(asli)
        self.assertEqual(baru["reasoning"], {"effort": "high"})
        self.assertEqual(info["reasoning_summary"], 0)

    def test_hanya_summary_reasoning_dihapus(self) -> None:
        baru, _ = self.mod.bersihkan_payload({"reasoning": {"summary": "auto"}})
        self.assertNotIn("reasoning", baru)

    def test_reasoning_bukan_dict_tidak_error(self) -> None:
        baru, info = self.mod.bersihkan_payload({"reasoning": "none"})
        self.assertEqual(baru["reasoning"], "none")
        self.assertEqual(info["reasoning_summary"], 0)

    def test_payload_asli_tidak_dimutasi(self) -> None:
        asli = {"reasoning": {"effort": "none", "summary": "none"}}
        self.mod.bersihkan_payload(asli)
        self.assertIn("summary", asli["reasoning"])

    def test_log_menyebut_reasoning_dibuang(self) -> None:
        teks = self.mod.ringkas_log(
            "/v1/responses", {"model": "m"},
            {"reasoning_summary": 1, "status": 200})
        self.assertIn("reasoning.summary=dibuang", teks)


class TestBuangWebSearch(unittest.TestCase):
    """Gateway menolak tool `type: web_search` (400/3051)."""

    def setUp(self) -> None:
        self.mod = importlib.import_module("modules.codex_cutad.shim")

    def test_web_search_dibuang_function_dipertahankan(self) -> None:
        baru, jumlah = self.mod.buang_tool_tak_didukung(
            {"tools": [{"type": "web_search"}, {"type": "function",
                                                "name": "f"}]})
        self.assertEqual([t["type"] for t in baru["tools"]], ["function"])
        self.assertEqual(jumlah, 1)

    def test_tanpa_web_search_tidak_berubah(self) -> None:
        asli = {"tools": [{"type": "function", "name": "f"}]}
        baru, jumlah = self.mod.buang_tool_tak_didukung(asli)
        self.assertEqual(baru["tools"], asli["tools"])
        self.assertEqual(jumlah, 0)

    def test_tanpa_tools_aman(self) -> None:
        baru, jumlah = self.mod.buang_tool_tak_didukung({"model": "m"})
        self.assertEqual(baru, {"model": "m"})
        self.assertEqual(jumlah, 0)

    def test_payload_asli_tidak_dimutasi(self) -> None:
        asli = {"tools": [{"type": "web_search"}]}
        self.mod.buang_tool_tak_didukung(asli)
        self.assertEqual(len(asli["tools"]), 1)

    def test_bersihkan_payload_melaporkan_web_search(self) -> None:
        _, info = self.mod.bersihkan_payload(
            {"tools": [{"type": "web_search"}]})
        self.assertEqual(info["web_search"], 1)


class TestBuangFieldTakDidukung(unittest.TestCase):
    """Gateway menolak `store` (422/body.store) dan `previous_response_id`."""

    def setUp(self) -> None:
        self.mod = importlib.import_module("modules.codex_cutad.shim")

    def test_store_false_dibuang(self) -> None:
        baru, jumlah = self.mod.buang_field_tak_didukung(
            {"model": "m", "store": False})
        self.assertNotIn("store", baru)
        self.assertEqual(jumlah, 1)

    def test_store_true_dibuang(self) -> None:
        baru, jumlah = self.mod.buang_field_tak_didukung({"store": True})
        self.assertNotIn("store", baru)
        self.assertEqual(jumlah, 1)

    def test_previous_response_id_dibuang(self) -> None:
        baru, jumlah = self.mod.buang_field_tak_didukung(
            {"previous_response_id": "resp_1"})
        self.assertNotIn("previous_response_id", baru)
        self.assertEqual(jumlah, 1)

    def test_keduanya_dibuang_sekaligus(self) -> None:
        baru, jumlah = self.mod.buang_field_tak_didukung(
            {"store": False, "previous_response_id": "r", "model": "m"})
        self.assertEqual(baru, {"model": "m"})
        self.assertEqual(jumlah, 2)

    def test_tanpa_field_terlarang_tidak_berubah(self) -> None:
        asli = {"model": "m", "stream": True}
        baru, jumlah = self.mod.buang_field_tak_didukung(asli)
        self.assertEqual(baru, asli)
        self.assertEqual(jumlah, 0)

    def test_payload_asli_tidak_dimutasi(self) -> None:
        asli = {"store": False, "previous_response_id": "r"}
        self.mod.buang_field_tak_didukung(asli)
        self.assertIn("store", asli)

    def test_bersihkan_payload_melaporkan_store(self) -> None:
        baru, info = self.mod.bersihkan_payload({"store": False})
        self.assertNotIn("store", baru)
        self.assertEqual(info["store"], 1)

    def test_log_menyebut_store_dibuang(self) -> None:
        teks = self.mod.ringkas_log(
            "/v1/responses", {"model": "m"}, {"store": 1, "status": 200})
        self.assertIn("store=dibuang", teks)


class TestNormalisasiEffort(unittest.TestCase):
    """Gateway hanya menerima none/low/high/xhigh/max; `medium` wajib dipetakan."""

    def setUp(self) -> None:
        self.mod = importlib.import_module("modules.codex_cutad.shim")

    def test_medium_dipetakan_ke_high(self) -> None:
        baru, perubahan = self.mod.normalisasi_effort(
            {"reasoning": {"effort": "medium"}})
        self.assertEqual(baru["reasoning"], {"effort": "high"})
        self.assertEqual(perubahan, [("medium", "high")])

    def test_effort_didukung_tidak_berubah(self) -> None:
        for nilai in ("none", "low", "high", "xhigh", "max"):
            baru, perubahan = self.mod.normalisasi_effort(
                {"reasoning": {"effort": nilai}})
            self.assertEqual(baru["reasoning"]["effort"], nilai)
            self.assertEqual(perubahan, [])

    def test_effort_tak_dikenal_jadi_high(self) -> None:
        baru, perubahan = self.mod.normalisasi_effort(
            {"reasoning": {"effort": "sedang"}})
        self.assertEqual(baru["reasoning"]["effort"], "high")
        self.assertEqual(perubahan, [("sedang", "high")])

    def test_tanpa_reasoning_aman(self) -> None:
        baru, perubahan = self.mod.normalisasi_effort({"model": "m"})
        self.assertEqual(baru, {"model": "m"})
        self.assertEqual(perubahan, [])

    def test_reasoning_bukan_dict_aman(self) -> None:
        baru, perubahan = self.mod.normalisasi_effort({"reasoning": "auto"})
        self.assertEqual(baru["reasoning"], "auto")
        self.assertEqual(perubahan, [])

    def test_reasoning_tanpa_effort_aman(self) -> None:
        baru, perubahan = self.mod.normalisasi_effort(
            {"reasoning": {"summary": "auto"}})
        self.assertEqual(perubahan, [])

    def test_effort_bukan_string_aman(self) -> None:
        baru, perubahan = self.mod.normalisasi_effort(
            {"reasoning": {"effort": 3}})
        self.assertEqual(baru["reasoning"]["effort"], 3)
        self.assertEqual(perubahan, [])

    def test_payload_asli_tidak_dimutasi(self) -> None:
        asli = {"reasoning": {"effort": "medium"}}
        self.mod.normalisasi_effort(asli)
        self.assertEqual(asli["reasoning"]["effort"], "medium")

    def test_bersihkan_payload_melaporkan_effort(self) -> None:
        baru, info = self.mod.bersihkan_payload(
            {"reasoning": {"effort": "medium", "summary": "auto"}})
        self.assertEqual(baru["reasoning"], {"effort": "high"})
        self.assertEqual(info["effort"], [("medium", "high")])
        self.assertEqual(info["reasoning_summary"], 1)

    def test_log_menyebut_effort_dipetakan(self) -> None:
        teks = self.mod.ringkas_log(
            "/v1/responses", {"model": "m"},
            {"effort": [("medium", "high")], "status": 200})
        self.assertIn("effort=medium->high", teks)


class TestKontrakPayload(unittest.TestCase):
    """Payload mentah Codex 0.167.1 -> hanya field yang dikenal gateway."""

    def setUp(self) -> None:
        self.mod = importlib.import_module("modules.codex_cutad.shim")

    def payload_codex(self) -> dict:
        return {
            "model": "deepseek-v4-pro",
            "instructions": "x",
            "input": [{"type": "message", "role": "developer",
                       "content": [{"type": "input_text", "text": "i"}]}],
            "stream": True,
            "store": False,
            "include": ["reasoning.encrypted_content"],
            "prompt_cache_key": "k",
            "parallel_tool_calls": True,
            "tool_choice": "auto",
            "previous_response_id": "resp_1",
            "reasoning": {"effort": "medium", "summary": "auto"},
            "tools": [
                {"type": "web_search"},
                {"type": "namespace", "name": "ns",
                 "tools": [{"type": "function", "name": "f"}]},
            ],
        }

    def test_hasil_bersih_sesuai_kontrak(self) -> None:
        baru, info = self.mod.bersihkan_payload(self.payload_codex())
        self.assertNotIn("store", baru)
        self.assertNotIn("previous_response_id", baru)
        self.assertEqual(baru["reasoning"], {"effort": "high"})
        self.assertEqual([t["type"] for t in baru["tools"]], ["function"])
        self.assertEqual(baru["input"][0]["role"], "system")
        self.assertEqual(info["tambahan"], [])

    def test_semua_key_hasil_ada_di_daftar_kontrak(self) -> None:
        baru, _ = self.mod.bersihkan_payload(self.payload_codex())
        asing = [k for k in baru if k not in self.mod.KEY_KONTRAK]
        self.assertEqual(asing, [])

    def test_key_tak_dikenal_dilaporkan(self) -> None:
        baru, info = self.mod.bersihkan_payload({"model": "m", "foo_bar": 1})
        self.assertIn("foo_bar", baru)
        self.assertEqual(info["tambahan"], ["foo_bar"])

    def test_log_menyebut_param_tambahan(self) -> None:
        teks = self.mod.ringkas_log(
            "/v1/responses", {"model": "m"},
            {"tambahan": ["foo_bar"], "status": 200})
        self.assertIn("param_tambahan=foo_bar", teks)


class TestEksposModul(unittest.TestCase):
    """Aturan repo: setiap modul diekspos lewat `__init__.py`."""

    def test_paket_mengekspos_shim(self) -> None:
        paket = importlib.import_module("modules.codex_cutad")
        self.assertIs(paket.shim, shim)

    def test_paket_mengekspos_config_codex(self) -> None:
        paket = importlib.import_module("modules.codex_cutad")
        cfg = importlib.import_module("modules.codex_cutad.config_codex")
        self.assertIs(paket.config_codex, cfg)

    def test_all_terdaftar(self) -> None:
        paket = importlib.import_module("modules.codex_cutad")
        for nama in ("shim", "config_codex"):
            self.assertIn(nama, paket.__all__)


class TestServerEndToEnd(unittest.TestCase):
    """Shim dijalankan sungguhan; upstream diganti handler lokal (tanpa jaringan)."""

    def test_responses_developer_ditulis_ulang_dan_diteruskan(self) -> None:
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        import json
        import threading
        import urllib.request

        tertangkap = {}

        class Upstream(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                panjang = int(self.headers.get("content-length", 0))
                tertangkap["path"] = self.path
                tertangkap["auth"] = self.headers.get("authorization")
                tertangkap["body"] = json.loads(self.rfile.read(panjang))
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                self.wfile.write(b"event: response.completed\ndata: {}\n\n")

            def log_message(self, *a):  # noqa: ANN002
                pass

        upstream = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
        upstream.daemon_threads = True
        threading.Thread(target=upstream.serve_forever, daemon=True).start()
        self.addCleanup(upstream.server_close)
        self.addCleanup(upstream.shutdown)

        base = "http://127.0.0.1:%d/v1" % upstream.server_address[1]
        server = shim.buat_server(port=0, base=base, token="rahasia-server")
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)

        url = "http://127.0.0.1:%d/v1/responses" % server.server_address[1]
        payload = {"model": "deepseek-v4-pro", "stream": True, "store": False,
                   "previous_response_id": "resp_1",
                   "input": [pesan("instruksi", "developer"),
                             pesan("halo", "user")]}
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode(), method="POST",
            headers={"Content-Type": "application/json",
                     "Accept": "text/event-stream",
                     "Authorization": "Bearer token-klien"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            isi = resp.read().decode()
            self.assertEqual(resp.status, 200)
            self.assertIn("response.completed", isi)

        self.assertEqual(tertangkap["path"], "/v1/responses")
        self.assertEqual(tertangkap["auth"], "Bearer rahasia-server")
        badan = tertangkap["body"]
        self.assertNotIn("previous_response_id", badan)
        self.assertEqual(badan["input"][0]["role"], "system")
        self.assertTrue(badan["stream"])
        self.assertNotIn("store", badan)

    def test_upstream_error_diteruskan_apa_adanya(self) -> None:
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        import json
        import threading
        import urllib.error
        import urllib.request

        class Upstream(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error":{"code":"request_rejected"}}')

            def log_message(self, *a):  # noqa: ANN002
                pass

        upstream = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
        upstream.daemon_threads = True
        threading.Thread(target=upstream.serve_forever, daemon=True).start()
        self.addCleanup(upstream.server_close)
        self.addCleanup(upstream.shutdown)

        base = "http://127.0.0.1:%d/v1" % upstream.server_address[1]
        server = shim.buat_server(port=0, base=base, token="t")
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)

        url = "http://127.0.0.1:%d/v1/responses" % server.server_address[1]
        req = urllib.request.Request(
            url, data=json.dumps({"model": "m", "input": "x"}).encode(),
            method="POST", headers={"Content-Type": "application/json"})
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=10)
        self.assertEqual(ctx.exception.code, 400)
        self.assertIn(b"request_rejected", ctx.exception.read())


if __name__ == "__main__":
    unittest.main()