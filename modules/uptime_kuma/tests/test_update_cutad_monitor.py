"""Tests untuk modules/uptime_kuma/update_cutad_monitor.py.

Script ini memperbaiki monitor yang sudah terdaftar di Uptime Kuma
(mis. monitor lama 'cutad - glm 5.2' yang URL-nya salah: ai.cutad.com).
Spek nilai benar diambil dari tests/test_check_cutad.py.
"""
import importlib
import json
import os
import unittest
from unittest import mock

update = importlib.import_module("modules.uptime_kuma.update_cutad_monitor")


class TestTarget(unittest.TestCase):
    def test_target_memakai_url_dan_model_dari_spek(self) -> None:
        self.assertEqual(update.TARGET["url"], "https://ai.cutad.web.id/v1/chat/completions")
        self.assertEqual(update.TARGET["body"]["model"], "z-ai/glm-5.2")
        self.assertEqual(update.TARGET["type"], "keyword")
        self.assertEqual(update.TARGET["keyword"], "PONG")

    def test_target_tidak_memakai_domain_lama(self) -> None:
        self.assertNotIn("ai.cutad.com", json.dumps(update.TARGET))


class TestPerbaiki(unittest.TestCase):
    def test_payload_update_mengganti_url_model_dan_header(self) -> None:
        monitor_db = {
            "id": 1,
            "name": "cutad - glm 5.2",
            "type": "http",
            "url": "https://ai.cutad.com",
            "method": "GET",
            "headers": None,
            "body": None,
            "keyword": None,
        }

        payload = update.payload_update(monitor_db, "token-tes")

        self.assertEqual(payload["id"], 1)
        self.assertEqual(payload["name"], "cutad - glm 5.2")  # nama dipertahankan
        self.assertEqual(payload["type"], "keyword")
        self.assertEqual(payload["url"], "https://ai.cutad.web.id/v1/chat/completions")
        self.assertEqual(payload["method"], "POST")
        self.assertEqual(payload["keyword"], "PONG")
        self.assertEqual(json.loads(payload["body"])["model"], "z-ai/glm-5.2")
        self.assertEqual(
            json.loads(payload["headers"])["Authorization"], "Bearer token-tes"
        )
        # field wajib skema monitor tetap ada
        self.assertEqual(payload["accepted_statuscodes_json"], '["200-299"]')
        self.assertIn("conditions", payload)

    def test_body_dan_header_lama_ditimpa_bukan_dibiarkan(self) -> None:
        monitor_db = {
            "id": 1,
            "name": "cutad - glm 5.2",
            "type": "http",
            "url": "https://ai.cutad.com",
            "headers": '{"Authorization":"Bearer token-lama"}',
            "body": '{"model":"model-lama"}',
        }

        payload = update.payload_update(monitor_db, "token-baru")

        self.assertNotIn("model-lama", payload["body"])
        self.assertNotIn("token-lama", payload["headers"])


class TestPerbaikiMonitor(unittest.TestCase):
    def _klien(self, jawaban):
        """Klien socketio palsu: emit(event, payload, ack) -> langsung panggil ack."""
        klien = mock.Mock()

        def emit(event, payload, ack=None):
            if ack:
                ack(jawaban)

        klien.emit.side_effect = emit
        return klien

    def test_memanggil_socket_editMonitor(self) -> None:
        klien = self._klien({"ok": True, "msg": "Saved."})
        monitor_db = {
            "id": 1,
            "name": "cutad - glm 5.2",
            "type": "http",
            "url": "https://ai.cutad.com",
        }

        hasil = update.perbaiki_monitor(klien, monitor_db, "token-tes")

        self.assertTrue(hasil["ok"])
        self.assertEqual(klien.emit.call_args[0][0], "editMonitor")
        self.assertEqual(klien.emit.call_args[0][1]["url"], update.TARGET["url"])

    def test_gagal_ditandai_tidak_ok(self) -> None:
        klien = self._klien({"ok": False, "msg": "Monitor not found"})

        hasil = update.perbaiki_monitor(klien, {"id": 9, "name": "x"}, "token")

        self.assertFalse(hasil["ok"])
        self.assertIn("not found", hasil["msg"])


if __name__ == "__main__":
    unittest.main()
