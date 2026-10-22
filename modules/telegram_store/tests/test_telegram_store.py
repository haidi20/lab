from __future__ import annotations

import os
from unittest.mock import patch
from pathlib import Path
import tempfile
import unittest

from modules.telegram_store import (
    DigiflazzClient,
    InMemoryOrderStore,
    TelegramStoreBot,
    TelegramStoreService,
    load_env_file,
)
from modules.telegram_store.cli import build_bot_from_env


class FakeTransport:
    def __init__(self, responses: dict[tuple[str, str], dict[str, object]]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def __call__(self, method: str, url: str, payload: dict[str, object]) -> dict[str, object]:
        self.calls.append((method, url, payload))
        key = (method, url)
        if key not in self.responses:
            raise AssertionError(f"Unexpected request: {method} {url}")
        return self.responses[key]


class FakeDigiflazz:
    def __init__(self) -> None:
        self.orders: list[tuple[str, str, str]] = []

    def balance(self) -> int:
        return 250_000

    def price_list(self, code: str | None = None) -> list[dict[str, object]]:
        products = [
            {
                "buyer_sku_code": "BRIZZI5",
                "product_name": "Brizzi 5",
                "category": "E-Money",
                "brand": "BRIZZI",
                "seller_name": "Digiflazz",
                "price": 6_200,
                "buyer_product_status": True,
                "seller_product_status": True,
            },
            {
                "buyer_sku_code": "PLN100",
                "product_name": "Token PLN 100",
                "category": "PLN",
                "brand": "PLN",
                "seller_name": "Digiflazz",
                "price": 11_500,
                "buyer_product_status": True,
                "seller_product_status": True,
            },
        ]
        if code:
            return [item for item in products if item["buyer_sku_code"] == code]
        return products

    def create_transaction(
        self,
        buyer_sku_code: str,
        customer_no: str,
        ref_id: str,
        testing: bool = False,
    ) -> dict[str, object]:
        self.orders.append((buyer_sku_code, customer_no, ref_id))
        return {
            "ref_id": ref_id,
            "status": "Pending",
            "message": "Transaksi sedang diproses",
            "buyer_sku_code": buyer_sku_code,
            "customer_no": customer_no,
            "price": 6_200,
            "testing": testing,
        }

class FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, *args) -> bool:
        return False


class TelegramStoreTests(unittest.TestCase):
    def test_digiflazz_client_uses_required_buyer_signatures(self) -> None:
        transport = FakeTransport(
            {
                ("POST", "https://api.digiflazz.com/v1/price-list"): {"data": []},
                ("POST", "https://api.digiflazz.com/v1/transaction"): {
                    "data": {"ref_id": "INV-1", "status": "Pending"}
                },
            }
        )
        client = DigiflazzClient(username="store-user", api_key="api-key", transport=transport)

        client.price_list()
        client.create_transaction("BRIZZI5", "08123456789", "INV-1")

        self.assertEqual(transport.calls[0][2]["cmd"], "price")
        self.assertEqual(transport.calls[1][2]["buyer_sku_code"], "BRIZZI5")
        self.assertEqual(transport.calls[1][2]["customer_no"], "08123456789")
        self.assertEqual(transport.calls[1][2]["ref_id"], "INV-1")

    def test_store_lists_products_with_markup_and_orders_as_buyer(self) -> None:
        digiflazz = FakeDigiflazz()
        orders = InMemoryOrderStore()
        service = TelegramStoreService(digiflazz, markup_percent=10, orders=orders)

        products = service.list_products("PLN")
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]["sale_price"], 12_650)

        order = service.order("BRIZZI5", "08123456789")
        self.assertTrue(order["invoice"].startswith("HN-"))
        self.assertEqual(order["status"], "Pending")
        self.assertEqual(digiflazz.orders[0][0], "BRIZZI5")
        self.assertEqual(digiflazz.orders[0][1], "08123456789")
        self.assertEqual(orders.find(order["invoice"])["invoice"], order["invoice"])

    def test_bot_replies_with_store_commands(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[tuple[int, str]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/start"}})
        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/produk BRIZZI"}})
        purchase = service.order("BRIZZI5", "08123456789")
        bot.handle_update(
            {"message": {"chat": {"id": 101}, "text": f"/status {purchase['invoice']}"}}
        )

        self.assertIn("@hn_assistent_bot", sent[0][1])
        self.assertIn("Brizzi 5", sent[1][1])
        self.assertIn("Rp 6.820", sent[1][1])
        self.assertIn(purchase["invoice"], sent[2][1])

    def test_bot_accepts_product_alias(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[tuple[int, str]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/product BRIZZI"}})

        self.assertIn("Brizzi 5", sent[0][1])

    def test_bot_accepts_indonesian_command_aliases(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[tuple[int, str]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/bantuan"}})
        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/produk BRIZZI"}})
        purchase = service.order("BRIZZI5", "08123456789")
        bot.handle_update(
            {"message": {"chat": {"id": 101}, "text": f"/cekstatus {purchase['invoice']}"}}
        )

        self.assertIn("Selamat datang", sent[0][1])
        self.assertIn("Brizzi 5", sent[1][1])
        self.assertIn(purchase["invoice"], sent[2][1])

    def test_start_shows_menu_buttons(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[tuple[int, str, dict[str, object] | None]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append(
                (chat_id, text, reply_markup)
            ),
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/start"}})

        markup = sent[0][2]
        self.assertIsNotNone(markup)
        rows = markup["inline_keyboard"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(rows[0]), 2)
        self.assertEqual(len(rows[1]), 1)
        row_texts = {button["text"] for row in rows for button in row}
        self.assertIn("Lihat Produk", row_texts)
        self.assertIn("Beli Produk", row_texts)
        self.assertIn("Cek Status", row_texts)
        self.assertNotIn("Saldo", row_texts)

    def test_callback_query_triggers_command(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[tuple[int, str]] = []
        answered: list[str] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
            answer_callback_query=lambda query_id: answered.append(query_id),
        )

        bot.handle_update(
            {
                "callback_query": {
                    "id": "cb-1",
                    "data": "/produk",
                    "message": {"chat": {"id": 101}},
                }
            }
        )

        self.assertIn("Brizzi 5", sent[0][1])
        self.assertEqual(answered, ["cb-1"])

    def test_set_my_commands_registers_indonesian_menu(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text: None,
        )

        with patch("modules.telegram_store.bot.urllib.request.urlopen") as fake_urlopen:
            fake_urlopen.return_value = FakeResponse(b'{"ok": true}')
            bot.set_my_commands()

        request = fake_urlopen.call_args[0][0]
        self.assertIn("/setMyCommands", request.full_url)
        self.assertIn(b'"produk"', request.data)
        self.assertIn(b'Lihat daftar produk', request.data)
        self.assertNotIn(b'"saldo"', request.data)

    def test_run_registers_commands_before_polling(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text: None,
        )
        calls: list[str] = []
        bot.set_my_commands = lambda: calls.append("commands")

        def stop_polling(offset: int = 0) -> list[dict[str, object]]:
            raise KeyboardInterrupt

        bot.get_updates = stop_polling
        with self.assertRaises(KeyboardInterrupt):
            bot.run()

        self.assertEqual(calls, ["commands"])

    def test_load_env_file_sets_missing_bot_config(self) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as handle:
            handle.write(
                "TELEGRAM_BOT_TOKEN=token-abc\n"
                "DIGIFLAZZ_USERNAME=store-user\n"
                "DIGIFLAZZ_API_KEY=api-key\n"
            )
            path = handle.name
        try:
            os.environ.pop("TELEGRAM_BOT_TOKEN", None)
            os.environ.pop("DIGIFLAZZ_USERNAME", None)
            os.environ.pop("DIGIFLAZZ_API_KEY", None)
            load_env_file(path)
            self.assertEqual(os.environ["TELEGRAM_BOT_TOKEN"], "token-abc")
            self.assertEqual(os.environ["DIGIFLAZZ_USERNAME"], "store-user")
            self.assertEqual(os.environ["DIGIFLAZZ_API_KEY"], "api-key")
        finally:
            os.unlink(path)

    def test_build_bot_from_env_uses_hn_assistent_bot(self) -> None:
        env_path = Path(tempfile.gettempdir()) / "telegram_store_test.env"
        env_path.write_text(
            "TELEGRAM_BOT_TOKEN=token-abc\n"
            "TELEGRAM_BOT_USERNAME=@hn_assistent_bot\n"
            "DIGIFLAZZ_USERNAME=store-user\n"
            "DIGIFLAZZ_API_KEY=api-key\n",
            encoding="utf-8",
        )
        try:
            os.environ.pop("TELEGRAM_BOT_TOKEN", None)
            os.environ.pop("TELEGRAM_BOT_USERNAME", None)
            os.environ.pop("DIGIFLAZZ_USERNAME", None)
            os.environ.pop("DIGIFLAZZ_API_KEY", None)
            bot = build_bot_from_env(env_path=env_path)
            self.assertEqual(bot.bot_username, "@hn_assistent_bot")
        finally:
            env_path.unlink(missing_ok=True)

    def test_build_bot_from_env_allows_missing_digiflazz(self) -> None:
        env_path = Path(tempfile.gettempdir()) / "telegram_store_no_digiflazz.env"
        env_path.write_text("TELEGRAM_BOT_TOKEN=token-abc\n", encoding="utf-8")
        try:
            os.environ.pop("TELEGRAM_BOT_TOKEN", None)
            os.environ.pop("DIGIFLAZZ_USERNAME", None)
            os.environ.pop("DIGIFLAZZ_API_KEY", None)
            bot = build_bot_from_env(env_path=env_path)

            self.assertEqual(bot.bot_username, "@hn_assistent_bot")
            sent: list[tuple[int, str]] = []
            bot.send_message = lambda chat_id, text, reply_markup=None: sent.append((chat_id, text))
            bot.handle_update({"message": {"chat": {"id": 101}, "text": "/start"}})
            bot.handle_update({"message": {"chat": {"id": 101}, "text": "/produk"}})
            bot.handle_update({"message": {"chat": {"id": 101}, "text": "/saldo"}})

            self.assertIn("Selamat datang", sent[0][1])
            self.assertIn("Produk tidak ditemukan", sent[1][1])
            self.assertIn("belum tersedia", sent[2][1])
        finally:
            env_path.unlink(missing_ok=True)
