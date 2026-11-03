"""Tests untuk perbandingan dua URL chat completion di modul 9router."""
import importlib
import json
import os
import unittest
from unittest import mock

ping_module = importlib.import_module("modules.9router.ping")
TARGETS = ping_module.TARGETS
kirim_chat = ping_module.kirim_chat
bandingkan = ping_module.bandingkan
format_ringkasan = ping_module.format_ringkasan


class TestTargets(unittest.TestCase):
    def test_ada_dua_target(self) -> None:
        self.assertEqual(len(TARGETS), 2)

    def test_target_pertama_cutad_dengan_authorization(self) -> None:
        target = TARGETS[0]

        self.assertEqual(target["url"], "https://ai.cutad.web.id/v1/chat/completions")
        self.assertIn("Authorization", target["headers"])
        self.assertTrue(target["headers"]["Authorization"].startswith("Bearer "))

    def test_target_kedua_lokal_tanpa_authorization(self) -> None:
        target = TARGETS[1]

        self.assertEqual(target["url"], "http://127.0.0.1:20128/v1/chat/completions")
        self.assertNotIn("Authorization", target["headers"])
        self.assertNotIn("authorization", target["headers"])

    def test_model_target_kedua_nama_yang_valid_di_9router(self) -> None:
        # /v1/models 9router tidak punya "z-ai/glm-5.2"; nama valid: cd/z-ai/glm-5.2
        self.assertEqual(TARGETS[1]["model"], "cd/z-ai/glm-5.2")

    def test_model_target_pertama_cutad(self) -> None:
        self.assertEqual(TARGETS[0]["model"], "z-ai/glm-5.2")

    def test_setiap_target_punya_model(self) -> None:
        for target in TARGETS:
            self.assertIn("model", target)
            self.assertTrue(target["model"])

    def test_token_cutad_dibaca_dari_environment(self) -> None:
        module_name = ping_module.__name__
        with mock.patch.dict(os.environ, {"CUTAD_API_KEY": "token-tes"}, clear=True):
            reloaded_module = importlib.import_module(module_name)
            reloaded_module = importlib.reload(reloaded_module)

        try:
            self.assertEqual(
                reloaded_module.TARGETS[0]["headers"]["Authorization"],
                "Bearer token-tes",
            )
        finally:
            importlib.reload(ping_module)

    def test_tidak_ada_token_hardcoded(self) -> None:
        with open(ping_module.__file__, encoding="utf-8") as module_file:
            source = module_file.read()

        self.assertNotIn("cag_va8", source)


class TestKirimChat(unittest.TestCase):
    def test_sukses_mengembalikan_hasil_terstruktur(self) -> None:
        response = mock.Mock(status_code=200)
        response.json.return_value = {
            "choices": [{"message": {"content": "Halo!"}}]
        }

        with mock.patch.object(ping_module.requests, "post", return_value=response) as post:
            hasil = kirim_chat(TARGETS[0])

        self.assertTrue(hasil["ok"])
        self.assertEqual(hasil["status_code"], 200)
        self.assertEqual(hasil["url"], TARGETS[0]["url"])
        self.assertEqual(hasil["content"], "Halo!")
        self.assertNotIn("error", hasil)
        post.assert_called_once()
        self.assertEqual(post.call_args.kwargs["json"]["model"], TARGETS[0]["model"])

    def test_gagal_mengembalikan_status_dan_teks(self) -> None:
        response = mock.Mock(status_code=404)
        response.json.side_effect = ValueError("bukan json")
        response.text = "Not Found"

        with mock.patch.object(ping_module.requests, "post", return_value=response):
            hasil = kirim_chat(TARGETS[0])

        self.assertFalse(hasil["ok"])
        self.assertEqual(hasil["status_code"], 404)
        self.assertIn("Not Found", hasil["error"])

    def test_error_jaringan_ditangkap(self) -> None:
        with mock.patch.object(
            ping_module.requests,
            "post",
            side_effect=ping_module.requests.exceptions.ConnectionError("refused"),
        ):
            hasil = kirim_chat(TARGETS[1])

        self.assertFalse(hasil["ok"])
        self.assertIn("refused", hasil["error"])

    def test_target_kedua_dikirim_tanpa_header_authorization(self) -> None:
        response = mock.Mock(status_code=200)
        response.json.return_value = {"choices": [{"message": {"content": "ok"}}]}

        with mock.patch.object(ping_module.requests, "post", return_value=response) as post:
            kirim_chat(TARGETS[1])

        headers = post.call_args.kwargs["headers"]
        self.assertNotIn("Authorization", headers)
        self.assertNotIn("authorization", headers)

    def test_body_dengan_artefak_sse_data_done_tetap_terbaca(self) -> None:
        # 9router kadang mengembalikan JSON utuh + "data: [DONE]" di ekor body
        body = (
            '{"id":"x","object":"chat.completion",'
            '"choices":[{"index":0,"message":{"role":"assistant","content":"Halo!"},'
            '"finish_reason":"stop"}]}data: [DONE]'
        )
        response = mock.Mock(status_code=200)
        response.json.side_effect = json.JSONDecodeError("Extra data", body, len(body) - 12)
        response.text = body

        with mock.patch.object(ping_module.requests, "post", return_value=response):
            hasil = kirim_chat(TARGETS[1])

        self.assertTrue(hasil["ok"])
        self.assertEqual(hasil["status_code"], 200)
        self.assertEqual(hasil["content"], "Halo!")

    def test_header_content_type_selalu_ada(self) -> None:
        response = mock.Mock(status_code=200)
        response.json.return_value = {"choices": [{"message": {"content": "ok"}}]}

        for target in TARGETS:
            with mock.patch.object(ping_module.requests, "post", return_value=response) as post:
                kirim_chat(target)

            self.assertEqual(post.call_args.kwargs["headers"]["Content-Type"], "application/json")


class TestBandingkan(unittest.TestCase):
    def test_bandingkan_memanggil_kedua_url(self) -> None:
        response = mock.Mock(status_code=200)
        response.json.return_value = {"choices": [{"message": {"content": "ok"}}]}

        with mock.patch.object(ping_module.requests, "post", return_value=response) as post:
            hasil = bandingkan()

        self.assertEqual(len(hasil), 2)
        self.assertEqual(post.call_count, 2)
        urls = [h["url"] for h in hasil]
        self.assertEqual(
            urls,
            [
                "https://ai.cutad.web.id/v1/chat/completions",
                "http://127.0.0.1:20128/v1/chat/completions",
            ],
        )


class TestFormatRingkasan(unittest.TestCase):
    HASIL_CONTOH = [
        {
            "url": "https://ai.cutad.web.id/v1/chat/completions",
            "ok": True,
            "status_code": 200,
            "content": "halo",
            "durasi": 1.5,
        },
        {
            "url": "http://127.0.0.1:20128/v1/chat/completions",
            "ok": False,
            "status_code": 503,
            "error": "boom",
            "durasi": 0.02,
        },
    ]

    def test_setiap_url_ditandai_berhasil_atau_gagal(self) -> None:
        baris = format_ringkasan(self.HASIL_CONTOH)
        teks = "\n".join(baris)

        self.assertIn("BERHASIL", teks)
        self.assertIn("GAGAL", teks)

        baris_url1 = [b for b in baris if "ai.cutad.web.id" in b][0]
        self.assertIn("✅", baris_url1)
        self.assertIn("200", baris_url1)

        baris_url2 = [b for b in baris if "127.0.0.1:20128" in b][0]
        self.assertIn("❌", baris_url2)
        self.assertIn("503", baris_url2)

    def test_ada_baris_kesimpulan_url_yang_berhasil_dan_gagal(self) -> None:
        baris = format_ringkasan(self.HASIL_CONTOH)
        teks = "\n".join(baris)

        self.assertIn("URL BERHASIL: https://ai.cutad.web.id/v1/chat/completions", teks)
        self.assertIn("URL GAGAL   : http://127.0.0.1:20128/v1/chat/completions", teks)

    def test_semua_gagal(self) -> None:
        hasil = [
            {"url": "http://x", "ok": False, "status_code": None, "error": "e", "durasi": 0.1}
        ]
        teks = "\n".join(format_ringkasan(hasil))

        self.assertIn("URL BERHASIL: tidak ada", teks)
        self.assertIn("URL GAGAL   : http://x", teks)


if __name__ == "__main__":
    unittest.main()
