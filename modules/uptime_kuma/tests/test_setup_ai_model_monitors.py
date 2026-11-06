"""Tests untuk modules/uptime_kuma/setup_ai_model_monitors.py.

3 monitor keyword "hallo", satu per model AI: z-ai/glm-5.2,
glm-5.3-flash, deepseek-v4-pro. Semua POST ke /v1/chat/completions
ai.cutad.web.id dengan Authorization Bearer CUTAD_API_KEY.
"""
import importlib
import json
import os
import unittest
from unittest import mock

setup_ai = importlib.import_module("modules.uptime_kuma.setup_ai_model_monitors")


class TestDaftarMonitor(unittest.TestCase):
    def test_tiga_monitor_satu_per_model(self) -> None:
        monitors = setup_ai.monitors("token-tes")
        self.assertEqual(len(monitors), 3)
        models = {m["body"]["model"] for m in monitors}
        self.assertEqual(
            models, {"z-ai/glm-5.2", "glm-5.3-flash", "deepseek-v4-pro"}
        )

    def test_setiap_monitor_post_keyword_hallo_ke_chat_completions(self) -> None:
        for monitor in setup_ai.monitors("token-tes"):
            self.assertEqual(monitor["type"], "keyword")
            self.assertEqual(
                monitor["url"], "https://ai.cutad.web.id/v1/chat/completions"
            )
            self.assertEqual(monitor["method"], "POST")
            self.assertEqual(monitor["keyword"], "hallo")
            # Prompt memaksa balasan lowercase persis 'hallo' (keyword
            # di-scan case-sensitive oleh Uptime Kuma).
            self.assertIn("hallo", monitor["body"]["messages"][0]["content"])
            self.assertFalse(monitor["invertKeyword"])

    def test_setiap_monitor_pakai_bearer_api_key(self) -> None:
        for monitor in setup_ai.monitors("token-tes"):
            self.assertEqual(monitor["headers"]["Authorization"], "Bearer token-tes")
            self.assertIn("Content-Type", monitor["headers"])

    def test_nama_monitor_menyebut_model_dan_hallo(self) -> None:
        for monitor in setup_ai.monitors("token-tes"):
            self.assertIn(monitor["body"]["model"], monitor["name"])
            self.assertIn("hallo", monitor["name"])

    def test_tanpa_api_key_raises(self) -> None:
        with mock.patch.dict(os.environ, {"CUTAD_API_KEY": ""}, clear=True):
            with self.assertRaises(RuntimeError):
                setup_ai.monitors()


class TestSocketPayload(unittest.TestCase):
    def test_body_dan_header_diserialize_jadi_string_json(self) -> None:
        monitor = setup_ai.monitors("token-tes")[0]
        payload = setup_ai.socket_payload(monitor)

        self.assertIsInstance(payload["body"], str)
        self.assertEqual(
            json.loads(payload["body"])["model"], monitor["body"]["model"]
        )
        self.assertEqual(
            json.loads(payload["headers"])["Authorization"], "Bearer token-tes"
        )
        self.assertEqual(payload["keyword"], "hallo")
        self.assertEqual(payload["httpBodyEncoding"], "json")

    def test_field_wajib_skema_monitor_uptime_kuma_lengkap(self) -> None:
        payload = setup_ai.socket_payload(setup_ai.monitors("token-tes")[0])
        for wajib in (
            "name",
            "type",
            "interval",
            "retryInterval",
            "timeout",
            "maxretries",
            "accepted_statuscodes",
            "conditions",
            "method",
            "active",
            "parent",
            "notificationIDList",
        ):
            self.assertIn(wajib, payload, f"field wajib hilang: {wajib}")
        self.assertEqual(payload["active"], True)
        # handler `add` Kuma v3 menuntut array (bukan string _json).
        self.assertEqual(payload["accepted_statuscodes"], ["200-299"])
        self.assertEqual(payload["conditions"], [])


class TestDaftarkan(unittest.TestCase):
    def _klien(self, jawaban):
        klien = mock.Mock()

        def emit(event, payload, callback=None):
            if callback:
                callback(jawaban)

        klien.emit.side_effect = emit
        return klien

    def test_emit_add_dengan_callback_dan_rekap_ok(self) -> None:
        klien = self._klien({"ok": True, "msg": "Added Successfully."})

        hasil = setup_ai.daftarkan(klien, setup_ai.monitors("token-tes"))

        self.assertEqual(len(hasil), 3)
        self.assertTrue(all(h["ok"] for h in hasil))
        self.assertEqual(klien.emit.call_count, 3)
        self.assertEqual(klien.emit.call_args_list[0][0][0], "add")
        self.assertIn("model", json.loads(klien.emit.call_args_list[0][0][1]["body"]))

    def test_gagal_ditandai_tidak_ok(self) -> None:
        klien = self._klien({"ok": False, "msg": "Monitor already exists."})

        hasil = setup_ai.daftarkan(klien, setup_ai.monitors("token-tes"))

        self.assertFalse(all(h["ok"] for h in hasil))
        self.assertIn("already exists", hasil[0]["msg"])


class TestHapusMonitorTerlanjur(unittest.TestCase):
    def setUp(self) -> None:
        import sqlite3

        self.db = sqlite3.connect(":memory:")
        self.db.execute(
            "create table monitor (id integer primary key, name text)"
        )
        self.db.executemany(
            "insert into monitor (id, name) values (?, ?)",
            [
                (2, "glm-5.3-flash via chat/completions (hallo)"),
                (3, "deepseek-v4-pro via chat/completions (hallo)"),
                (9, "monitor lain"),
            ],
        )
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()

    def test_ambil_id_hanya_monitor_dengan_nama_sama(self) -> None:
        nama = [m["name"] for m in setup_ai.monitors("token-tes")]
        ids = setup_ai.ambil_id_monitor(self.db, nama)
        self.assertEqual(sorted(ids), [2, 3])

    def test_kosong_bila_tidak_ada_yang_cocok(self) -> None:
        ids = setup_ai.ambil_id_monitor(self.db, ["tidak ada"])
        self.assertEqual(ids, [])

    def test_hapus_monitor_emit_deleteMonitor_dengan_callback(self) -> None:
        klien = mock.Mock()

        def emit(event, *args, callback=None):
            if callback:
                callback({"ok": True, "msg": "Deleted."})

        klien.emit.side_effect = emit

        hasil = setup_ai.hapus_monitor(klien, 2)

        self.assertEqual(klien.emit.call_args[0][0], "deleteMonitor")
        self.assertEqual(klien.emit.call_args[0][1], 2)
        self.assertTrue(hasil["ok"])


if __name__ == "__main__":
    unittest.main()
