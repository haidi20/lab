"""Tests untuk modul uptime_kuma.

Meng-cover:
- Clone github uptime-kuma di modules/uptime_kuma (1 folder, tanpa install)
- .env berisi CUTAD_API_KEY
- Definisi monitor (url ai.cutad, api key/koneksi HTTPS, ping, model)
"""
import importlib
import json
import os
import unittest


def _module():
    return importlib.import_module("modules.uptime_kuma.check_cutad")


def _dir_clone():
    return os.path.dirname(_module().__file__)


class TestModulTerpasang(unittest.TestCase):
    """Uptime kuma di-clone langsung di modules/uptime_kuma (1 folder saja)."""

    def test_clone_berada_langsung_di_folder_modul(self) -> None:
        self.assertTrue(
            os.path.isdir(_dir_clone()),
            "modules/uptime_kuma harus berisi clone uptime-kuma",
        )

    def test_tidak_ada_nesting_folder_ganda(self) -> None:
        # Dulu sempat uptime_kuma/uptime-kuma; sekarang harus 1 folder saja.
        self.assertFalse(
            os.path.exists(os.path.join(_dir_clone(), "uptime-kuma")),
            "Tidak boleh ada nesting uptime_kuma/uptime-kuma",
        )

    def test_clone_berisi_file_inti_uptime_kuma(self) -> None:
        for wajib in ("package.json", "server", "src", "db"):
            self.assertTrue(
                os.path.exists(os.path.join(_dir_clone(), wajib)),
                f"file/dir khas uptime-kuma tidak ditemukan: {wajib}",
            )

    def test_package_json_uptime_kuma_valid(self) -> None:
        with open(
            os.path.join(_dir_clone(), "package.json"), encoding="utf-8"
        ) as f:
            pkg = json.load(f)
        self.assertEqual(pkg.get("name"), "uptime-kuma")
        self.assertIn("scripts", pkg)

    def test_git_dir_clone_masih_ada(self) -> None:
        # clone sungguhan dari github (bukan sekadar copy source)
        self.assertTrue(os.path.isdir(os.path.join(_dir_clone(), ".git")))

    def test_node_modules_sudah_terinstall(self) -> None:
        # Kuma sekarang sudah di-install dan berjalan (per 2026-11-06);
        # aturan lama "jangan install dulu" tidak berlaku lagi.
        self.assertTrue(
            os.path.exists(os.path.join(_dir_clone(), "node_modules")),
            "node_modules harus ada (Kuma sudah ter-install & running)",
        )

    def test_env_memiliki_cutad_api_key(self) -> None:
        env_path = os.path.join(_dir_clone(), "..", "..", ".env")
        with open(env_path, encoding="utf-8") as f:
            isi = f.read()
        self.assertRegex(isi, r"(?m)^CUTAD_API_KEY=\S")


class TestMonitor(unittest.TestCase):
    def test_ping_cutad_url_dan_monitor_https_api(self) -> None:
        monitors = _module().MONITORS
        berdasar_nama = {m["name"]: m for m in monitors}

        ping = berdasar_nama["Ping jaringan ke ai.cutad.web.id"]
        self.assertEqual(ping["type"], "ping")
        self.assertEqual(ping["hostname"], "ai.cutad.web.id")

        https = berdasar_nama["API key & koneksi HTTPS ai.cutad.web.id"]
        self.assertEqual(https["type"], "http")
        self.assertEqual(https["url"], "https://ai.cutad.web.id")
        self.assertEqual(https["httpFormat"], "any-valid-status")
        self.assertIn("Authorization", https["headers"])

    def test_monitor_model_z_ai_glm_5_2_chat_completions(self) -> None:
        monitor = {m["name"]: m for m in _module().MONITORS}[
            "z-ai/glm-5.2 via chat/completions"
        ]
        self.assertEqual(monitor["type"], "keyword")
        self.assertEqual(
            monitor["url"], "https://ai.cutad.web.id/v1/chat/completions"
        )
        self.assertEqual(monitor["body"]["model"], "z-ai/glm-5.2")
        self.assertEqual(monitor["keyword"], "PONG")
        self.assertIn("Authorization", monitor["headers"])

    def test_monitor_z_ai_glm_5_2_respons_codex(self) -> None:
        monitor = {m["name"]: m for m in _module().MONITORS}[
            "z-ai/glm-5.2 via responses (jalur Codex)"
        ]
        self.assertEqual(monitor["type"], "keyword")
        self.assertEqual(monitor["url"], "https://ai.cutad.web.id/v1/responses")
        self.assertEqual(monitor["body"]["model"], "z-ai/glm-5.2")

    def test_monitor_glm_5_3_flash_chat_completions(self) -> None:
        monitor = {m["name"]: m for m in _module().MONITORS}[
            "glm-5.3-flash via chat/completions"
        ]
        self.assertEqual(monitor["type"], "keyword")
        self.assertEqual(monitor["body"]["model"], "glm-5.3-flash")

    def test_monitor_deepseek_v4_pro_via_codex(self) -> None:
        monitor = {m["name"]: m for m in _module().MONITORS}[
            "glm-5.3-flash / deepseek-v4-pro via Codex"
        ]
        self.assertEqual(monitor["type"], "keyword")
        self.assertEqual(monitor["url"], "https://ai.cutad.web.id/v1/responses")

    def test_setiap_monitor_http_punya_authorization(self) -> None:
        for monitor in _module().MONITORS:
            if monitor["type"] in ("http", "keyword"):
                self.assertIn("Authorization", monitor["headers"])
                self.assertTrue(
                    monitor["headers"]["Authorization"].startswith("Bearer ")
                )
                self.assertIn("Content-Type", monitor["headers"])

    def test_tidak_ada_cag_token_hardcoded(self) -> None:
        with open(_module().__file__, encoding="utf-8") as f:
            source = f.read()
        self.assertNotIn("cag_", source)


if __name__ == "__main__":
    unittest.main()