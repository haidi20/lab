from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from modules.telegram_store import TelegramStoreService
from modules.telegram_store.store import SQLiteOrderStore
from modules.telegram_store.webhook import verify_digiflazz_signature


class FakeDigiflazz:
    def __init__(self) -> None:
        self.orders: list[tuple[str, str, str, bool]] = []

    def balance(self) -> int:
        return 1_000_000

    def set_mode(self, mode: str) -> None:
        self.mode = mode

    def price_list(self, code: str | None = None) -> list[dict[str, object]]:
        return [{
            "buyer_sku_code": "SKU1", "product_name": "Product", "category": "Pulsa",
            "brand": "TELKOMSEL", "price": 10_000, "buyer_product_status": True,
            "seller_product_status": True,
        }]

    def create_transaction(self, sku: str, customer_no: str, ref_id: str, testing: bool = False) -> dict[str, object]:
        self.orders.append((sku, customer_no, ref_id, testing))
        return {"ref_id": ref_id, "status": "Pending", "message": "", "price": 10_000}


class PaymentInfrastructureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.path = Path(tempfile.TemporaryDirectory().name + ".sqlite3")
        self.store = SQLiteOrderStore(self.path)
        self.digiflazz = FakeDigiflazz()
        self.service = TelegramStoreService(self.digiflazz, orders=self.store)

    def test_orders_survive_store_recreation(self) -> None:
        order = self.service.order("SKU1", "081234554320")
        reopened = SQLiteOrderStore(self.path)

        self.assertEqual(order["invoice"], reopened.find(order["invoice"])["invoice"])

    def test_status_update_records_one_success_entry_and_is_idempotent(self) -> None:
        order = self.service.order("SKU1", "081234554320")
        self.service.apply_status(order["invoice"], {"status": "Sukses", "message": "OK"})
        self.service.apply_status(order["invoice"], {"status": "Sukses", "message": "OK"})

        self.assertEqual("Sukses", self.store.find(order["invoice"])["status"])
        entries = self.store.ledger_entries(order["invoice"])
        self.assertEqual(1, len(entries))
        self.assertEqual(-11_100, entries[0]["amount"])

    def test_failed_status_records_reversal_entry(self) -> None:
        order = self.service.order("SKU1", "081234554320")
        self.service.apply_status(order["invoice"], {"status": "Sukses"})
        self.service.apply_status(order["invoice"], {"status": "Gagal", "message": "FAILED"})

        entries = self.store.ledger_entries(order["invoice"])
        self.assertEqual(2, len(entries))
        self.assertEqual(-11_100, entries[0]["amount"])
        self.assertEqual(11_100, entries[1]["amount"])

    def test_webhook_signature_validation(self) -> None:
        valid = hashlib.md5(b"userapi-keyinvoice-1").hexdigest()
        self.assertTrue(verify_digiflazz_signature("user", "api-key", "invoice-1", valid))
        self.assertFalse(verify_digiflazz_signature("user", "api-key", "invoice-1", "bad"))

    def test_webhook_updates_order_and_ignores_duplicate_events(self) -> None:
        order = self.service.order("SKU1", "081234554320")
        payload = {"ref_id": order["invoice"], "status": "Sukses", "message": "OK"}

        self.assertTrue(self.service.apply_webhook(payload, signature=None, trust_unauthenticated=True))
        self.assertFalse(self.service.apply_webhook(payload, signature=None, trust_unauthenticated=True))

        self.assertEqual("Sukses", self.store.find(order["invoice"])["status"])
        self.assertEqual(1, len(self.store.ledger_entries(order["invoice"])))

    def test_webhook_rejects_invalid_signature(self) -> None:
        order = self.service.order("SKU1", "081234554320")
        payload = {"ref_id": order["invoice"], "status": "Sukses"}

        self.assertFalse(self.service.apply_webhook(payload, signature="bad", trust_unauthenticated=False))
        self.assertEqual("Pending", self.store.find(order["invoice"])["status"])

    def test_mode_switch_clears_checkout_and_deposit_state(self) -> None:
        from modules.telegram_store.bot import TelegramStoreBot

        bot = TelegramStoreBot(
            token="token",
            service=self.service,
            send_message=lambda chat_id, text, reply_markup=None: None,
            answer_callback_query=lambda callback_query_id: None,
        )
        bot.handle_update({"callback_query": {"id": "1", "data": "/bank 200000 BCA", "message": {"chat": {"id": 101}}}})
        bot._selected_products[101] = {"buyer_sku_code": "SKU1"}

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/sandbox"}})

        self.assertEqual("sandbox", bot.mode)
        self.assertNotIn(101, bot._deposit_banks)
        self.assertNotIn(101, bot._selected_products)
        self.assertTrue(bot.service.testing)

    def test_same_transaction_ref_is_not_sent_twice(self) -> None:
        first = self.service.order("SKU1", "081234554320")
        second = self.service.order("SKU1", "081234554320")

        self.assertEqual(1, len(self.digiflazz.orders))
        self.assertEqual(first["invoice"], second["invoice"])

    def test_customer_number_is_validated_by_category(self) -> None:
        with self.assertRaisesRegex(ValueError, "nomor HP"):
            self.service.order("SKU1", "12345")

        self.assertEqual(0, len(self.digiflazz.orders))

    def test_client_timeout_is_configurable_and_transport_error_wrapped(self) -> None:
        from modules.telegram_store.client import DigiflazzClient

        def transport(method: str, url: str, payload: dict[str, object]) -> dict[str, object]:
            raise TimeoutError("timeout")

        client = DigiflazzClient("user", "key", transport=transport, timeout=7)
        self.assertEqual(7, client.timeout)

        with self.assertRaisesRegex(RuntimeError, "Digiflazz tidak merespons"):
            client.price_list()
