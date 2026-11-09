from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from pathlib import Path

from modules.telegram_store.cli import build_bot_from_env
from modules.telegram_store import TelegramStoreService
from modules.telegram_store.store import SQLiteOrderStore
from modules.telegram_store.webhook import verify_digiflazz_signature


class FakeDigiflazz:
    def __init__(self) -> None:
        self.orders: list[tuple[str, str, str, bool]] = []
        self.deposit_requests: list[tuple[int, str, str]] = []

    def balance(self) -> int:
        return 1_000_000

    def set_mode(self, mode: str) -> None:
        self.mode = mode

    def create_deposit(self, amount: int, bank: str, owner_name: str) -> dict[str, object]:
        self.deposit_requests.append((amount, bank, owner_name))
        return {
            "rc": "00",
            "bank": bank,
            "payment_method": "Virtual Account",
            "account_no": "123",
            "amount": amount,
            "notes": "DEP-1",
        }

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

    def test_webhook_events_are_persisted_and_deduplicated(self) -> None:
        order = self.service.order("SKU1", "081234554320")
        payload = {"ref_id": order["invoice"], "status": "Sukses", "message": "OK"}

        self.assertTrue(self.service.apply_webhook(payload, signature=None, trust_unauthenticated=True))
        self.assertFalse(self.service.apply_webhook(payload, signature=None, trust_unauthenticated=True))
        self.assertFalse(self.service.apply_webhook(payload, signature=None, trust_unauthenticated=True))

        reopened = SQLiteOrderStore(self.path)
        events = reopened.webhook_events()
        self.assertEqual(1, len(events))
        self.assertEqual(order["invoice"], events[0]["invoice"])
        self.assertEqual("Sukses", events[0]["status"])

    def test_invalid_webhook_does_not_create_persisted_event(self) -> None:
        order = self.service.order("SKU1", "081234554320")
        payload = {"ref_id": order["invoice"], "status": "Sukses"}

        self.assertFalse(self.service.apply_webhook(payload, signature="bad", trust_unauthenticated=False))

        self.assertEqual([], self.store.webhook_events())

    def test_status_change_records_persisted_audit_log(self) -> None:
        order = self.service.order("SKU1", "081234554320")
        self.service.apply_status(order["invoice"], {"status": "Sukses", "message": "OK"})
        self.service.apply_status(order["invoice"], {"status": "Sukses", "message": "OK"})

        reopened = SQLiteOrderStore(self.path)
        logs = reopened.audit_logs()
        self.assertEqual(1, len(logs))
        self.assertEqual(order["invoice"], logs[0]["invoice"])
        self.assertEqual("status", logs[0]["action"])
        self.assertEqual("Sukses", logs[0]["status"])

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

    def test_update_offset_persists_across_store_recreation(self) -> None:
        store = SQLiteOrderStore(self.path)

        self.assertEqual(0, store.get_update_offset())
        store.set_update_offset(123)

        reopened = SQLiteOrderStore(self.path)
        self.assertEqual(123, reopened.get_update_offset())

    def test_sqlite_is_configured_for_long_running_bot(self) -> None:
        store = SQLiteOrderStore(self.path)

        self.assertEqual("wal", store.connection.execute("PRAGMA journal_mode").fetchone()[0].lower())
        self.assertEqual(5000, store.connection.execute("PRAGMA busy_timeout").fetchone()[0])
        self.assertEqual(1, store.connection.execute("PRAGMA synchronous").fetchone()[0])

    def test_deposit_ticket_survives_store_recreation(self) -> None:
        ticket = self.service.create_deposit(100000, "BCA", "Haidi")
        self.assertEqual("DEP-1", ticket["notes"])
        self.assertEqual("BCA", ticket["bank"])
        self.assertEqual(100000, ticket["amount"])

        reopened = SQLiteOrderStore(self.path)
        saved = reopened.find_deposit("DEP-1")
        self.assertEqual(100000, saved["amount"])
        self.assertEqual("BCA", saved["bank"])
        self.assertEqual("Pending", saved["status"])

    def test_cli_build_uses_sqlite_orders_for_service(self) -> None:
        state_path = Path(tempfile.TemporaryDirectory().name + ".sqlite3")
        env_values = {
            "TELEGRAM_BOT_TOKEN": "token",
            "TELEGRAM_STORE_STATE_PATH": str(state_path),
            "PRODUCT_CATALOG_PATH": str(state_path.with_suffix(".products.sqlite3")),
        }
        for key, value in env_values.items():
            os.environ[key] = value
        with tempfile.TemporaryDirectory() as cwd:
            current_cwd = Path.cwd()
            try:
                os.chdir(cwd)
                bot = build_bot_from_env(env_path=Path("missing.env"))
                self.assertIs(bot.service.orders, bot.update_offset_store)
                self.assertIsInstance(bot.service.orders, SQLiteOrderStore)
            finally:
                os.chdir(current_cwd)
        for key in env_values:
            os.environ.pop(key, None)
