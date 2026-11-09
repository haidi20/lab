from __future__ import annotations

import unittest

from modules.telegram_store.bot import TelegramStoreBot
from modules.telegram_store.tests.test_telegram_store import FakeDigiflazz
from modules.telegram_store import TelegramStoreService


class PollingPayloadTests(unittest.TestCase):
    def test_invalid_get_updates_payload_does_not_stop_polling(self) -> None:
        service = TelegramStoreService(FakeDigiflazz())
        sent: list[tuple[int, str]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
            answer_callback_query=lambda callback_query_id: None,
        )
        bot.set_my_commands = lambda: None

        class Polling:
            def __init__(self) -> None:
                self.responses = [None, ["invalid", {"update_id": 1, "message": {"chat": {"id": 101}, "text": "/health"}}], KeyboardInterrupt()]

            def __call__(self, offset: int = 0) -> object:
                response = self.responses.pop(0)
                if isinstance(response, BaseException):
                    raise response
                return response

        bot.get_updates = Polling()
        bot.run()

        self.assertEqual(1, len(sent))
        self.assertIn("<b>Status Bot</b>", sent[0][1])

    def test_invalid_update_id_is_skipped_without_stopping_polling(self) -> None:
        service = TelegramStoreService(FakeDigiflazz())
        sent: list[tuple[int, str]] = []
        offsets: list[int] = []

        class StateStore:
            def get_update_offset(self) -> int:
                return 0

            def set_update_offset(self, value: int) -> None:
                offsets.append(value)

        bot = TelegramStoreBot(
            token="token",
            service=service,
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
            answer_callback_query=lambda callback_query_id: None,
            update_offset_store=StateStore(),
        )
        bot.set_my_commands = lambda: None

        class Polling:
            def __init__(self) -> None:
                self.responses = [
                    [{"update_id": "broken"}, {"update_id": 1, "message": {"chat": {"id": 101}, "text": "/health"}}],
                    KeyboardInterrupt(),
                ]

            def __call__(self, offset: int = 0) -> list[dict[str, object]]:
                response = self.responses.pop(0)
                if isinstance(response, BaseException):
                    raise response
                return response

        bot.get_updates = Polling()
        bot.run()

        self.assertEqual([2], offsets)
        self.assertEqual(1, len(sent))
        self.assertIn("<b>Status Bot</b>", sent[0][1])
