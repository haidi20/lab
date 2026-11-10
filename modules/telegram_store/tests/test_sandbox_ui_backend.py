from __future__ import annotations

import os
import unittest
import uuid
from time import sleep
from pathlib import Path
from tempfile import TemporaryDirectory

from modules.telegram_store.bot import TelegramStoreBot
from modules.telegram_store.bot import load_env_file
from modules.telegram_store.catalog import SQLiteProductCatalog
from modules.telegram_store.client import DigiflazzClient
from modules.telegram_store.service import TelegramStoreService
from modules.telegram_store.store import SQLiteOrderStore


class SandboxUiBackendFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if os.environ.get("DIGIFLAZZ_REAL_TESTS", "0") != "1":
            raise unittest.SkipTest("Real Digiflazz tests require DIGIFLAZZ_REAL_TESTS=1")
        load_env_file(".env")
        cls.username = os.environ.get("DIGIFLAZZ_USERNAME", "")
        production_key = os.environ.get("DIGIFLAZZ_API_KEY", "")
        development_key = os.environ.get("DIGIFLAZZ_DEVELOPMENT_KEY", "")
        if not all([cls.username, production_key, development_key]):
            raise unittest.SkipTest("Kredensial sandbox Digiflazz belum lengkap")
        cls.client = DigiflazzClient(
            username=cls.username,
            api_key=production_key,
            development_key=development_key,
        )
        cls.client.set_mode("sandbox")
        cls.directory = TemporaryDirectory()
        cls.addClassCleanup(cls.directory.cleanup)
        cls.store = SQLiteOrderStore(Path(cls.directory.name) / "sandbox-flow.sqlite3")
        cls.catalog = SQLiteProductCatalog(Path("modules/telegram_store/data/products.sqlite3"))
        cls.service = TelegramStoreService(
            cls.client,
            orders=cls.store,
            markup_percent=10,
            catalog=cls.catalog,
            digiflazz_username=cls.username,
            digiflazz_api_key=development_key,
        )
        cls.service.testing = True
        catalog_products = cls.client.price_list()
        if catalog_products:
            cls.catalog.replace_all(catalog_products)
        cls.sent: list[tuple[int, str, dict[str, object] | None]] = []
        cls.bot = TelegramStoreBot(
            token="sandbox-flow-token",
            service=cls.service,
            send_message=lambda chat_id, text, reply_markup=None: cls.sent.append((chat_id, text, reply_markup)),
            answer_callback_query=lambda callback_query_id: None,
            mode="sandbox",
        )

    def setUp(self) -> None:
        self.sent.clear()

    def test_deposit_ui_creates_real_sandbox_va_tickets_for_each_bank(self) -> None:
        initial_balance = self.client.balance()
        self.assertGreaterEqual(initial_balance, 0)

        self.bot.handle_update({"message": {"chat": {"id": 810001}, "text": "/saldo"}})
        inventory = self.sent[0][2]
        self.assertIsNotNone(inventory, self.sent)
        callbacks = [
            str(button["callback_data"])
            for row in inventory.get("inline_keyboard", [])
            for button in row
        ]
        self.assertIn("/isidaldo 200000", callbacks)
        self.assertIn("/nominal", callbacks)

        for bank in ("Flip", "ShopeePay"):
            chat_id = 810002 if bank == "Flip" else 810003
            self.bot.handle_update({"callback_query": {"id": f"cb-{bank}", "data": "/isidaldo 200000", "message": {"chat": {"id": chat_id}}}})
            self.bot.handle_update({"callback_query": {"id": f"cb-bank-{bank}", "data": f"/bank 200000 {bank}", "message": {"chat": {"id": chat_id}}}})
            self.bot.handle_update({"message": {"chat": {"id": chat_id}, "text": "Pemilik Sandbox Real"}})

            result = self.sent[-1][1]
            self.assertIn("Bank Transfer", result)
            self.assertIn("Tiket Deposit Dibuat", result)
            self.assertIn(bank, result)
            ticket_note = result.split("Berita transfer: <code>", 1)[1].split("</code>", 1)[0]
            ticket = self.store.find_deposit(ticket_note)
            self.assertEqual("Pending", ticket["status"])
            self.assertGreaterEqual(int(ticket["amount"]), 200_000)

    def test_product_ui_creates_real_sandbox_order_until_status_and_persistence(self) -> None:
        products = self.client.price_list("s10")
        if not products and self.service.catalog is not None:
            products = [
                product
                for product in self.service.catalog.get_all()
                if product.get("buyer_sku_code") == "s10"
            ]
        if not products:
            sleep(1)
            products = self.client.price_list("s10")
        self.assertTrue(products)
        sku = str(products[0]["buyer_sku_code"])

        self.bot.handle_update({"message": {"chat": {"id": 820001}, "text": "/produk s10"}})
        print("PRODUCT_SENT", self.sent, flush=True)
        inventory = next((markup for _, _, markup in self.sent if markup is not None), None)
        self.assertIsNotNone(inventory)
        product_callbacks = [
            str(button["callback_data"])
            for row in inventory.get("inline_keyboard", [])
            for button in row
        ]
        self.assertIn(f"/pilih {sku}", product_callbacks)

        self.bot.handle_update({"callback_query": {"id": "cb-product", "data": f"/pilih {sku}", "message": {"chat": {"id": 820001}}}})
        if not any("Produk dipilih" in message for _, message, _ in self.sent):
            self.bot.handle_update({"message": {"chat": {"id": 820001}, "text": f"/beli {sku} 081234554320"}})
        result = self.sent[-1][1]
        self.assertIn("Pesanan Dibuat", result)
        self.assertTrue(any(f"Status: <b>{status}</b>" in result for status in ("Sukses", "Pending", "Gagal")))

        invoice = result.split("Invoice: <code>", 1)[1].split("</code>", 1)[0]
        saved = self.store.find(invoice)
        self.assertEqual(sku, saved["sku"])
        self.assertEqual("081234554320", saved["customer_no"])
        self.assertIn(saved["status"], {"Sukses", "Pending"})
        self.assertTrue(saved["invoice"].startswith("HN-"))

        self.bot.handle_update({"message": {"chat": {"id": 820001}, "text": f"/status {invoice}"}})
        status_message = self.sent[-1][1]
        self.assertIn("Status Transaksi", status_message)
        self.assertTrue(any(f"Status: <b>{status}</b>" in status_message for status in ("Sukses", "Pending", "Gagal")))
        self.assertIn(self.service.status(invoice)["status"], {"Sukses", "Pending", "Gagal"})


if __name__ == "__main__":
    unittest.main()
