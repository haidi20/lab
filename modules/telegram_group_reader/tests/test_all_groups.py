import unittest

from modules.telegram_group_reader import (
    InMemoryTelegramBackend,
    TelegramGroupInfo,
    TelegramGroupReader,
    TelegramMessage,
)


class TestAllGroups(unittest.TestCase):
    def test_lists_all_groups_from_backend(self) -> None:
        groups = [
            TelegramGroupInfo(group_id="-1001", title="Klinik Dev", group_type="group"),
            TelegramGroupInfo(group_id="-1002", title="Info Channel", group_type="channel"),
        ]
        backend = InMemoryTelegramBackend([], groups=groups)
        reader = TelegramGroupReader(backend=backend, chat_id="")

        result = reader.get_all_groups()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].title, "Klinik Dev")
        self.assertEqual(result[1].group_type, "channel")

    def test_fetches_messages_from_all_groups(self) -> None:
        groups = [
            TelegramGroupInfo(group_id="g1", title="Group 1", group_type="group"),
            TelegramGroupInfo(group_id="g2", title="Group 2", group_type="group"),
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

        result = reader.get_all_messages_from_all_groups()

        self.assertEqual(len(result), 2)
        self.assertEqual(result["Group 1"][0].text, "Halo")
        self.assertEqual(result["Group 2"][0].text, "Siap")

    def test_counts_total_messages_across_all_groups(self) -> None:
        groups = [
            TelegramGroupInfo(group_id="g1", title="Group 1", group_type="group"),
            TelegramGroupInfo(group_id="g2", title="Group 2", group_type="group"),
        ]
        backend = InMemoryTelegramBackend(
            [],
            groups=groups,
            messages_by_group={
                "g1": [
                    TelegramMessage(message_id=1, sender="A", text="a"),
                    TelegramMessage(message_id=2, sender="B", text="b"),
                ],
                "g2": [TelegramMessage(message_id=3, sender="C", text="c")],
            },
        )
        reader = TelegramGroupReader(backend=backend, chat_id="")

        total = reader.count_messages_all_groups()

        self.assertEqual(total, 3)

    def test_fetch_all_groups_with_since_filters(self) -> None:
        now = datetime(2026, 10, 21, tzinfo=timezone.utc)
        old = now - timedelta(days=20)
        recent = now - timedelta(days=1)
        groups = [TelegramGroupInfo(group_id="g1", title="Group 1", group_type="group")]
        backend = InMemoryTelegramBackend(
            [],
            groups=groups,
            messages_by_group={
                "g1": [
                    TelegramMessage(message_id=1, sender="A", text="old", date=old),
                    TelegramMessage(message_id=2, sender="B", text="new", date=recent),
                ],
            },
        )
        reader = TelegramGroupReader(backend=backend, chat_id="")

        result = reader.get_all_messages_from_all_groups(since=now - timedelta(days=10))

        self.assertEqual(len(result["Group 1"]), 1)
        self.assertEqual(result["Group 1"][0].text, "new")


if __name__ == "__main__":
    unittest.main()
from datetime import datetime, timedelta, timezone

