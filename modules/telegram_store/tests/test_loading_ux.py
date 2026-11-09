from __future__ import annotations

import unittest

from modules.telegram_store.bot import TelegramStoreBot
from modules.telegram_store.tests.test_telegram_store import FakeDigiflazz
from modules.telegram_store import TelegramStoreService


class LoadingUxTests(unittest.TestCase):
    def test_provider_actions_show_loading_before_result(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[str] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            send_message=lambda chat_id, text, reply_markup=None: sent.append(text),
            answer_callback_query=lambda callback_query_id: None,
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/produk"}})

        self.assertIn("⏳ <b>Memuat produk…</b>", sent[0])
        self.assertIn("<b>Daftar Produk</b>", sent[-1])
        self.assertGreater(len(sent), 1)

    def test_status_action_shows_loading_before_result(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[str] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            send_message=lambda chat_id, text, reply_markup=None: sent.append(text),
            answer_callback_query=lambda callback_query_id: None,
        )
        service.orders.save({
            "invoice": "INV-1", "sku": "BRIZZI5", "customer_no": "081234554320",
            "product": "Brizzi 5", "price": 6200, "sale_price": 7570,
            "status": "Pending", "message": "",
        })
        service.digiflazz.status_responses = [{"status": "Sukses", "message": "OK"}]

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/status INV-1"}})

        self.assertIn("⏳ <b>Memeriksa status…</b>", sent[0])
        self.assertIn("Status: <b>Sukses</b>", sent[-1])

    def test_checkout_action_shows_loading_before_result(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[str] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            send_message=lambda chat_id, text, reply_markup=None: sent.append(text),
            answer_callback_query=lambda callback_query_id: None,
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/beli BRIZZI5 081234554320"}})

        self.assertIn("⏳ <b>Memproses pesanan…</b>", sent[0])
        self.assertIn("Pesanan Dibuat", sent[-1])

    def test_failed_loading_message_does_not_stop_product_processing(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[str] = []
        send_calls = 0

        def send_message(chat_id: int, text: str, reply_markup=None) -> None:
            nonlocal send_calls
            send_calls += 1
            if send_calls == 1:
                raise RuntimeError("loading message unavailable")
            sent.append(text)

        bot = TelegramStoreBot(
            token="token",
            service=service,
            send_message=send_message,
            answer_callback_query=lambda callback_query_id: None,
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/produk"}})

        self.assertEqual(1, len(sent))
        self.assertIn("<b>Daftar Produk</b>", sent[0])

    def test_failed_order_result_message_restores_checkout_state(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(balance=1_000_000), markup_percent=10)
        send_calls = 0

        def send_message(chat_id: int, text: str, reply_markup=None) -> None:
            nonlocal send_calls
            send_calls += 1
            if send_calls == 2:
                raise RuntimeError("result message unavailable")

        bot = TelegramStoreBot(
            token="token",
            service=service,
            send_message=send_message,
            answer_callback_query=lambda callback_query_id: None,
        )
        bot._selected_products[101] = {"buyer_sku_code": "BRIZZI5", "product_name": "Brizzi 5", "price": 6200}

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "081234554320"}})

        self.assertIn(101, bot._selected_products)
        self.assertEqual("BRIZZI5", bot._selected_products[101]["buyer_sku_code"])
        self.assertEqual(1, len(service.digiflazz.orders))

    def test_failed_status_result_message_does_not_crash_handler(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        send_calls = 0
        sent: list[str] = []

        def send_message(chat_id: int, text: str, reply_markup=None) -> None:
            nonlocal send_calls
            send_calls += 1
            if send_calls == 2:
                raise RuntimeError("status message unavailable")
            sent.append(text)

        bot = TelegramStoreBot(
            token="token",
            service=service,
            send_message=send_message,
            answer_callback_query=lambda callback_query_id: None,
        )
        service.orders.save({
            "invoice": "INV-1", "sku": "BRIZZI5", "customer_no": "081234554320",
            "product": "Brizzi 5", "price": 6200, "sale_price": 7570,
            "status": "Pending", "message": "",
        })
        service.digiflazz.status_responses = [{"status": "Sukses", "message": "OK"}]

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/status INV-1"}})

        self.assertEqual("Sukses", service.orders.find("INV-1")["status"])
        self.assertFalse(any("Digiflazz gagal diproses" in message for message in sent))
