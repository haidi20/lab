import asyncio
import unittest
from datetime import datetime, timedelta, timezone

from modules.telegram_group_reader import TelethonBackend


class FakeSender:
    def __init__(self, first_name: str = "", last_name: str = "", title: str = "") -> None:
        self.first_name = first_name
        self.last_name = last_name
        self.title = title


class FakeTelethonMessage:
    def __init__(
        self,
        message_id: int,
        text: str | None,
        sender: FakeSender | None,
        date: datetime | None = None,
    ) -> None:
        self.id = message_id
        self.text = text
        self._sender = sender
        self.date = date

    async def get_sender(self) -> FakeSender | None:
        return self._sender


class FakeTelethonClient:
    def __init__(self, messages: list[FakeTelethonMessage]) -> None:
        self._messages = messages
        self.started = False
        self._loop = asyncio.new_event_loop()
        self.last_chat_arg: object = None

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self._loop

    def is_connected(self) -> bool:
        return self.started

    def start(self) -> None:
        self.started = True

    def iter_messages(self, chat_id: str):
        self.last_chat_arg = chat_id

        async def generator():
            for message in self._messages:
                yield message

        return generator()


class TestTelethonBackend(unittest.TestCase):
    def test_maps_telethon_messages_to_telegram_message(self) -> None:
        sender = FakeSender(first_name="Andi", last_name="Pratama")
        client = FakeTelethonClient([FakeTelethonMessage(1, "Halo", sender)])
        backend = TelethonBackend(api_id=12345, api_hash="hash", client=client)

        messages = backend.fetch_messages("klinik-dev")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message_id, 1)
        self.assertEqual(messages[0].sender, "Andi Pratama")
        self.assertEqual(messages[0].text, "Halo")

    def test_maps_channel_title_as_sender(self) -> None:
        sender = FakeSender(title="Klinik Channel")
        client = FakeTelethonClient([FakeTelethonMessage(2, "Info", sender)])
        backend = TelethonBackend(api_id=12345, api_hash="hash", client=client)

        messages = backend.fetch_messages("klinik-dev")

        self.assertEqual(messages[0].sender, "Klinik Channel")

    def test_handles_media_message_without_text(self) -> None:
        client = FakeTelethonClient(
            [FakeTelethonMessage(3, None, FakeSender(first_name="Budi"))]
        )
        backend = TelethonBackend(api_id=12345, api_hash="hash", client=client)

        messages = backend.fetch_messages("klinik-dev")

        self.assertEqual(messages[0].text, "")

    def test_handles_unknown_sender(self) -> None:
        client = FakeTelethonClient([FakeTelethonMessage(4, "Siap", None)])
        backend = TelethonBackend(api_id=12345, api_hash="hash", client=client)

        messages = backend.fetch_messages("klinik-dev")

        self.assertEqual(messages[0].sender, "")

    def test_starts_disconnected_client_before_fetch(self) -> None:
        client = FakeTelethonClient([])
        backend = TelethonBackend(api_id=12345, api_hash="hash", client=client)

        backend.fetch_messages("klinik-dev")

        self.assertTrue(client.started)

    def test_stops_fetching_when_message_older_than_since(self) -> None:
        now = datetime(2026, 10, 21, 12, 0, 0, tzinfo=timezone.utc)
        ten_days_ago = now - timedelta(days=10)
        eleven_days_ago = now - timedelta(days=11)
        client = FakeTelethonClient(
            [
                FakeTelethonMessage(2, "baru", FakeSender(first_name="B"), date=ten_days_ago),
                FakeTelethonMessage(1, "lama", FakeSender(first_name="A"), date=eleven_days_ago),
            ]
        )
        backend = TelethonBackend(api_id=1, api_hash="h", client=client)

        messages = backend.fetch_messages("g", since=ten_days_ago)

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message_id, 2)

    def test_maps_message_date(self) -> None:
        when = datetime(2026, 10, 20, 8, 0, 0, tzinfo=timezone.utc)
        client = FakeTelethonClient(
            [FakeTelethonMessage(5, "halo", FakeSender(first_name="A"), date=when)]
        )
        backend = TelethonBackend(api_id=1, api_hash="h", client=client)

        messages = backend.fetch_messages("g")

        self.assertEqual(messages[0].date, when)

    def test_converts_numeric_group_id_to_int_for_entity_resolution(self) -> None:
        client = FakeTelethonClient([])
        backend = TelethonBackend(api_id=1, api_hash="h", client=client)

        backend.fetch_messages("-1004460260278")

        self.assertEqual(client.last_chat_arg, -1004460260278)


if __name__ == "__main__":
    unittest.main()
