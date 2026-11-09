from __future__ import annotations

import unittest

from modules.telegram_store.bot import TelegramStoreBot
from modules.telegram_store.service import TelegramStoreService
from modules.telegram_store.tests.test_telegram_store import FakeDigiflazz


class CallbackResilienceTests(unittest.TestCase):
    def test_failed_callback_acknowledgement_does_not_stop_action(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[str] = []

        bot = TelegramStoreBot(
            token="token",
            service=service,
            send_message=lambda chat_id, text, reply_markup=None: sent.append(text),
            answer_callback_query=lambda callback_query_id: (_ for _ in ()).throw(
                RuntimeError("callback acknowledgement unavailable")
            ),
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

        self.assertTrue(sent)
        self.assertTrue(any("<b>Daftar Produk</b>" in message for message in sent))


if __name__ == "__main__":
    unittest.main()
