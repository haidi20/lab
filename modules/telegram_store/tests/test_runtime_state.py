from __future__ import annotations

import unittest

from modules.telegram_store.bot import TelegramStoreBot
from modules.telegram_store.tests.test_telegram_store import FakeDigiflazz
from modules.telegram_store import TelegramStoreService


class RuntimeStateTests(unittest.TestCase):
    def test_expired_checkout_and_deposit_state_is_removed(self) -> None:
        bot = TelegramStoreBot(
            token="token",
            service=TelegramStoreService(FakeDigiflazz()),
            send_message=lambda chat_id, text, reply_markup=None: None,
            answer_callback_query=lambda callback_query_id: None,
        )
        chat_id = 101
        bot._catalog_numbers[chat_id] = []
        bot._selected_products[chat_id] = {"buyer_sku_code": "SKU1"}
        bot._deposit_amounts[chat_id] = 200000
        bot._deposit_banks[chat_id] = (200000, "BCA")
        bot._state_last_seen[chat_id] = 0

        bot.cleanup_expired_state(now=1799)
        self.assertIn(chat_id, bot._selected_products)
        bot.cleanup_expired_state(now=1800)

        self.assertNotIn(chat_id, bot._catalog_numbers)
        self.assertNotIn(chat_id, bot._selected_products)
        self.assertNotIn(chat_id, bot._deposit_amounts)
        self.assertNotIn(chat_id, bot._deposit_banks)

    def test_current_user_state_is_touched_and_not_expired_immediately(self) -> None:
        bot = TelegramStoreBot(
            token="token",
            service=TelegramStoreService(FakeDigiflazz()),
            send_message=lambda chat_id, text, reply_markup=None: None,
            answer_callback_query=lambda callback_query_id: None,
        )
        chat_id = 202

        bot.touch_state(chat_id, now=100)
        bot.cleanup_expired_state(now=1899)

        self.assertEqual(100, bot._state_last_seen[chat_id])

    def test_run_cleanup_removes_expired_state_between_updates(self) -> None:
        bot = TelegramStoreBot(
            token="token",
            service=TelegramStoreService(FakeDigiflazz()),
            send_message=lambda chat_id, text, reply_markup=None: None,
            answer_callback_query=lambda callback_query_id: None,
        )
        bot._selected_products[201] = {"buyer_sku_code": "SKU1"}
        bot._state_last_seen[201] = -1800
        class Polling:
            def __init__(self) -> None:
                self.responses = [([], False), (None, True)]

            def __call__(self, offset: int = 0) -> list[dict[str, object]]:
                updates, last = self.responses.pop(0)
                if last:
                    raise KeyboardInterrupt()
                return updates

        bot.update_offset_store = None
        bot.get_updates = Polling()
        bot.set_my_commands = lambda: None

        bot.set_my_commands = lambda: None

        bot.run()

        self.assertNotIn(201, bot._selected_products)
        self.assertNotIn(201, bot._state_last_seen)
