"""Tests untuk modules/uptime_kuma/setup_monitors.py.

Script ini yang men-daftarkan monitor ai.cutad ke Uptime Kuma yang sedang
berjalan (socket.io: login -> add per monitor).
"""
import importlib
import json
import os
import unittest
from unittest import mock

setup = importlib.import_module("modules.uptime_kuma.setup_monitors")


class TestPayloadMonitor(unittest.TestCase):
    def test_socket_payload_mengisi_field_wajib_uptime_kuma(self) -> None:
        monitor = {
            "name": "uji",
            "type": "http",
            "url": "https://ai.cutad.web.id",
            "method": "GET",
            "headers": {"Authorization": "Bearer x"},
            "interval": 120,
        }

        payload = setup.socket_payload(monitor)

        # field wajib minimal untuk tabel monitor Uptime Kuma
        for wajib in (
            "name",
            "type",
            "interval",
            "retryInterval",
            "timeout",
            "maxretries",
            "accepted_statuscodes_json",
            "conditions",
            "headers",
            "body",
            "method",
            "active",
        ):
            self.assertIn(wajib, payload, f"field wajib hilang: {wajib}")

        self.assertEqual(payload["name"], "uji")
        self.assertEqual(payload["active"], True)
        self.assertEqual(payload["accepted_statuscodes_json"], '["200-299"]')
        self.assertEqual(payload["conditions"], "[]")
        self.assertEqual(json.loads(payload["headers"]), {"Authorization": "Bearer x"})

    def test_body_dict_di_serialize_jadi_string_json(self) -> None:
        monitor = {
            "name": "glm",
            "type": "keyword",
            "url": "https://ai.cutad.web.id/v1/chat/completions",
            "method": "POST",
            "body": {"model": "glm-5.3-flash"},
            "keyword": "PONG",
        }

        payload = setup.socket_payload(monitor)

        self.assertIsInstance(payload["body"], str)
        self.assertEqual(json.loads(payload["body"])["model"], "glm-5.3-flash")
        self.assertEqual(payload["keyword"], "PONG")

    def test_ping_monitor_tidak_punya_url(self) -> None:
        payload = setup.socket_payload(
            {"name": "ping", "type": "ping", "hostname": "ai.cutad.web.id"}
        )
        self.assertEqual(payload["hostname"], "ai.cutad.web.id")
        self.assertEqual(payload["type"], "ping")


class TestKonfigurasi(unittest.TestCase):
    def test_base_url_default_localhost_3001(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(setup.base_url(), "http://127.0.0.1:3001")

    def test_base_url_bisa_dioverride_env(self) -> None:
        with mock.patch.dict(
            os.environ, {"UPTIME_KUMA_URL": "http://192.168.1.9:3001"}, clear=True
        ):
            self.assertEqual(setup.base_url(), "http://192.168.1.9:3001")

    def test_kredensial_wajib_dari_env(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"UPTIME_KUMA_USERNAME": "admin", "UPTIME_KUMA_PASSWORD": "rahasia"},
            clear=True,
        ):
            self.assertEqual(setup.kredensial(), ("admin", "rahasia"))

        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):
                setup.kredensial()


class TestDaftarMonitor(unittest.TestCase):
    def test_daftar_memanggil_add_untuk_setiap_monitor(self) -> None:
        monitors = [
            {"name": "a", "type": "ping", "hostname": "ai.cutad.web.id"},
            {"name": "b", "type": "http", "url": "https://ai.cutad.web.id"},
        ]
        klien = mock.Mock()
        klien.emit.return_value = {"ok": True, "msg": "Added Successfully."}

        hasil = setup.daftarkan(klien, monitors)

        self.assertEqual(len(hasil), 2)
        self.assertTrue(all(h["ok"] for h in hasil))
        self.assertEqual(klien.emit.call_count, 2)
        event_pertama = klien.emit.call_args_list[0][0][0]
        self.assertEqual(event_pertama, "add")
        # payload dipisah: emit("add", payload, callback)
        self.assertEqual(klien.emit.call_args_list[0][0][1]["name"], "a")

    def test_monitor_gagal_ditandai_tidak_ok(self) -> None:
        klien = mock.Mock()
        klien.emit.return_value = {"ok": False, "msg": "Monitor already exists."}

        hasil = setup.daftarkan(
            klien, [{"name": "a", "type": "ping", "hostname": "ai.cutad.web.id"}]
        )

        self.assertFalse(hasil[0]["ok"])
        self.assertIn("already exists", hasil[0]["msg"])


if __name__ == "__main__":
    unittest.main()