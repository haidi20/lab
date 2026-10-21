import os
import unittest
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from unittest.mock import patch

from modules.telegram_group_reader import (
    InMemoryTelegramBackend,
    SyncConfig,
    TelegramGroupInfo,
    TelegramGroupReader,
    TelegramMessage,
    default_since,
    load_env_file,
    run_sync,
)


class FakeStore:
    def __init__(self) -> None:
        self.saved_groups: list[TelegramGroupInfo] = []
        self.saved: dict[str, list[TelegramMessage]] = {}

    def save_groups(self, groups: list[TelegramGroupInfo]) -> None:
        self.saved_groups = list(groups)

    def save_messages(self, group_title: str, messages: list[TelegramMessage]) -> None:
        self.saved[group_title] = messages


class TestSync(unittest.TestCase):
    def test_run_sync_saves_groups_and_all_messages(self) -> None:
        groups = [
            TelegramGroupInfo(group_id="g1", title="Group A", group_type="group"),
            TelegramGroupInfo(group_id="g2", title="Group B", group_type="group"),
        ]
        backend = InMemoryTelegramBackend(
            [],
            groups=groups,
            messages_by_group={
                "g1": [TelegramMessage(message_id=1, sender="Andi", text="Halo")],
                "g2": [TelegramMessage(message_id=2, sender="Budi", text="Siap")],
            },
        )
        reader = TelegramGroupReader(backend=backend, chat_id="")
        store = FakeStore()

        result = run_sync(reader, store)

        self.assertEqual(len(store.saved_groups), 2)
        self.assertEqual(len(store.saved["Group A"]), 1)
        self.assertEqual(len(store.saved["Group B"]), 1)
        self.assertEqual(result["groups"], 2)
        self.assertEqual(result["messages"], 2)

    def test_sync_config_reads_from_env(self) -> None:
        env = {
            "TELEGRAM_API_ID": "123",
            "TELEGRAM_API_HASH": "hash-abc",
            "TELEGRAM_SESSION": "my_session",
            "MYSQL_HOST": "10.0.0.5",
            "MYSQL_PORT": "3307",
            "MYSQL_USER": "clinic",
            "MYSQL_PASSWORD": "secret",
            "MYSQL_DATABASE": "tg",
        }

        with patch.dict(os.environ, env):
            config = SyncConfig.from_env()

        self.assertEqual(config.api_id, 123)
        self.assertEqual(config.api_hash, "hash-abc")
        self.assertEqual(config.session, "my_session")
        self.assertEqual(config.mysql_host, "10.0.0.5")
        self.assertEqual(config.mysql_port, 3307)
        self.assertEqual(config.mysql_user, "clinic")
        self.assertEqual(config.mysql_password, "secret")
        self.assertEqual(config.mysql_database, "tg")

    def test_run_sync_with_since_filters_old_messages(self) -> None:
        now = datetime(2026, 10, 21, 12, 0, 0, tzinfo=timezone.utc)
        ten_days_ago = now - timedelta(days=10)
        eleven_days_ago = now - timedelta(days=11)
        groups = [TelegramGroupInfo(group_id="g1", title="Group A", group_type="group")]
        backend = InMemoryTelegramBackend(
            [],
            groups=groups,
            messages_by_group={
                "g1": [
                    TelegramMessage(message_id=1, sender="Lama", text="lama", date=eleven_days_ago),
                    TelegramMessage(message_id=2, sender="Baru", text="baru", date=ten_days_ago),
                ],
            },
        )
        reader = TelegramGroupReader(backend=backend, chat_id="")
        store = FakeStore()

        result = run_sync(reader, store, since=ten_days_ago)

        self.assertEqual(len(store.saved["Group A"]), 1)
        self.assertEqual(store.saved["Group A"][0].sender, "Baru")
        self.assertEqual(result["messages"], 1)

    def test_load_env_file_sets_missing_vars(self) -> None:
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile("w", suffix=".env", delete=False) as handle:
            handle.write("TELEGRAM_API_ID=999\nTELEGRAM_API_HASH=abc\n")
            path = Path(handle.name)

        try:
            with patch.dict(os.environ, {}, clear=True):
                load_env_file(path)
                self.assertEqual(os.environ["TELEGRAM_API_ID"], "999")
                self.assertEqual(os.environ["TELEGRAM_API_HASH"], "abc")
        finally:
            path.unlink()

    def test_default_since_uses_makassar_timezone(self) -> None:
        before = datetime.now(ZoneInfo("Asia/Makassar")) - timedelta(days=10)
        cutoff = default_since(days=10)
        after = datetime.now(ZoneInfo("Asia/Makassar")) - timedelta(days=10)

        self.assertIsNotNone(cutoff.tzinfo)
        self.assertLessEqual(before, cutoff)
        self.assertGreaterEqual(after, cutoff)


if __name__ == "__main__":
    unittest.main()
