from __future__ import annotations

import unittest

from modules.hermes_watchdog.notifier import TelegramNotifier


class TelegramNotifierTests(unittest.TestCase):
    def test_sends_message_to_configured_chat(self) -> None:
        calls = []

        def poster(url: str, payload: dict[str, object]) -> dict[str, object]:
            calls.append((url, payload))
            return {'ok': True}

        notifier = TelegramNotifier('token123', 101, poster=poster)
        notifier.send('Worker stale')

        self.assertEqual(len(calls), 1)
        url, payload = calls[0]
        self.assertIn('/bottoken123/sendMessage', url)
        self.assertEqual(payload['chat_id'], 101)
        self.assertEqual(payload['text'], 'Worker stale')

    def test_requires_token_and_chat(self) -> None:
        with self.assertRaises(ValueError):
            TelegramNotifier('', 101)
        with self.assertRaises(ValueError):
            TelegramNotifier('token', 0)
