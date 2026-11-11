from __future__ import annotations

import hashlib
import json
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from tempfile import TemporaryDirectory

from modules.telegram_store.service import TelegramStoreService
from modules.telegram_store.store import SQLiteOrderStore
from modules.telegram_store.tests.test_telegram_store import FakeDigiflazz
from modules.telegram_store.webhook_server import WebhookServer


class WebhookServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.store = SQLiteOrderStore(Path(self.directory.name) / "store.sqlite3")
        self.service = TelegramStoreService(
            FakeDigiflazz(balance=1_000_000),
            orders=self.store,
            markup_percent=10,
            digiflazz_username="sandbox-user",
            digiflazz_api_key="sandbox-key",
        )
        self.server = WebhookServer(
            ("127.0.0.1", 0),
            self.service,
            signature_header="X-Digiflazz-Sign",
        )
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        self.addCleanup(self.store.close)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def post(self, payload: dict[str, object], signature: str | None) -> tuple[int, dict[str, object]]:
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/webhook/digiflazz",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                **({} if signature is None else {"X-Digiflazz-Sign": signature}),
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=3) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read().decode("utf-8"))

    def signature_for(self, invoice: str) -> str:
        return hashlib.md5(f"sandbox-usersandbox-key{invoice}".encode("utf-8")).hexdigest()

    def test_health_endpoint_returns_component_status(self) -> None:
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/health", timeout=3) as response:
            result = json.loads(response.read().decode("utf-8"))

        self.assertEqual(200, response.status)
        self.assertTrue(result["ok"])

    def test_valid_webhook_updates_order_and_reports_duplicate(self) -> None:
        order = self.service.order("BRIZZI5", "081234554320")
        payload = {"ref_id": order["invoice"], "status": "Sukses", "message": "OK"}

        status, result = self.post(payload, self.signature_for(order["invoice"]))
        duplicate_status, duplicate = self.post(payload, self.signature_for(order["invoice"]))

        self.assertEqual(200, status)
        self.assertTrue(result["updated"])
        self.assertEqual(200, duplicate_status)
        self.assertFalse(duplicate["updated"])
        self.assertEqual("Sukses", self.store.find(order["invoice"])["status"])

    def test_missing_signature_is_rejected_without_update(self) -> None:
        order = self.service.order("BRIZZI5", "081234554320")
        payload = {"ref_id": order["invoice"], "status": "Sukses"}

        status, result = self.post(payload, None)

        self.assertEqual(401, status)
        self.assertFalse(result["ok"])
        self.assertEqual("Pending", self.store.find(order["invoice"])["status"])

    def test_invalid_signature_is_rejected_without_update(self) -> None:
        order = self.service.order("BRIZZI5", "081234554320")
        payload = {"ref_id": order["invoice"], "status": "Sukses"}

        status, result = self.post(payload, "invalid")

        self.assertEqual(401, status)
        self.assertFalse(result["ok"])
        self.assertEqual("Pending", self.store.find(order["invoice"])["status"])

    def test_unknown_invoice_returns_not_found(self) -> None:
        payload = {"ref_id": "UNKNOWN-INVOICE", "status": "Sukses"}

        status, result = self.post(payload, self.signature_for("UNKNOWN-INVOICE"))

        self.assertEqual(404, status)
        self.assertFalse(result["ok"])

    def test_invalid_json_returns_bad_request(self) -> None:
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/webhook/digiflazz",
            data=b"not-json",
            headers={"Content-Type": "application/json", "X-Digiflazz-Sign": "invalid"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=3):
                self.fail("Expected HTTP 400")
        except urllib.error.HTTPError as error:
            self.assertEqual(400, error.code)


if __name__ == "__main__":
    unittest.main()
