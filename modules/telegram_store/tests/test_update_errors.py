from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from modules.telegram_store.bot import TelegramStoreBot
from modules.telegram_store.store import SQLiteOrderStore
from modules.telegram_store.tests.test_telegram_store import FakeDigiflazz
from modules.telegram_store import TelegramStoreService


class UpdateErrorTests(unittest.TestCase):
    def test_failed_update_is_persisted_and_polling_continues(self) -> None:
        store = SQLiteOrderStore(Path(tempfile.TemporaryDirectory().name + ".sqlite3"))
        bot = TelegramStoreBot(
            token="token",
            service=TelegramStoreService(FakeDigiflazz()),
            send_message=lambda chat_id, text, reply_markup=None: None,
            answer_callback_query=lambda callback_query_id: None,
            update_offset_store=store,
        )
        bot.set_my_commands = lambda: None

        class FailingHandler:
            def __init__(self) -> None:
                self.calls = 0

            def __call__(self, update: dict[str, object]) -> None:
                self.calls += 1
                if self.calls == 1:
                    raise RuntimeError("update handler failed")

        failed_handler = FailingHandler()
        bot.handle_update = failed_handler

        class Polling:
            def __init__(self) -> None:
                self.responses = [[
                    {"update_id": 1},
                    {"update_id": 2},
                ], KeyboardInterrupt()]

            def __call__(self, offset: int = 0) -> list[dict[str, object]]:
                response = self.responses.pop(0)
                if isinstance(response, BaseException):
                    raise response
                return response

        bot.get_updates = Polling()
        bot.run()

        persisted = store.update_errors()
        self.assertEqual(1, len(persisted))
        self.assertEqual("update handler failed", persisted[0]["error"])
        self.assertEqual(1, persisted[0]["update_id"])

    def test_failed_error_persistence_does_not_stop_polling(self) -> None:
        store = SQLiteOrderStore(Path(tempfile.TemporaryDirectory().name + ".sqlite3"))

        class FailingStore:
            def get_update_offset(self) -> int:
                return 0

            def set_update_offset(self, value: int) -> None:
                return None

            def record_update_error(self, update_id: int, error: str, payload: object) -> bool:
                raise RuntimeError("error database unavailable")

        bot = TelegramStoreBot(
            token="token",
            service=TelegramStoreService(FakeDigiflazz()),
            send_message=lambda chat_id, text, reply_markup=None: None,
            answer_callback_query=lambda callback_query_id: None,
            update_offset_store=FailingStore(),
        )
        bot.set_my_commands = lambda: None

        failing_update_calls = 0

        def failing_update(update: dict[str, object]) -> None:
            nonlocal failing_update_calls
            failing_update_calls += 1
            raise RuntimeError("handler failed")

        bot.handle_update = failing_update

        class Polling:
            def __init__(self) -> None:
                self.responses = [[{"update_id": 1}], KeyboardInterrupt()]

            def __call__(self, offset: int = 0) -> list[dict[str, object]]:
                response = self.responses.pop(0)
                if isinstance(response, BaseException):
                    raise response
                return response

        bot.get_updates = Polling()

        bot.run()
        self.assertEqual(1, failing_update_calls)
