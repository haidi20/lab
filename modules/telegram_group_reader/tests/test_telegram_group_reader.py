import unittest

from modules.telegram_group_reader import (
    InMemoryTelegramBackend,
    TelegramMessage,
    TelegramGroupReader,
)


class TestTelegramGroupReader(unittest.TestCase):
    def test_reads_all_messages_from_backend(self) -> None:
        backend = InMemoryTelegramBackend(
            [
                TelegramMessage(message_id=1, sender="Andi", text="Halo semua"),
                TelegramMessage(message_id=2, sender="Budi", text="Siap"),
            ]
        )
        reader = TelegramGroupReader(backend=backend, chat_id="klinik-dev")

        messages = reader.get_all_messages()

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].sender, "Andi")
        self.assertEqual(messages[1].text, "Siap")

    def test_filters_messages_by_sender(self) -> None:
        backend = InMemoryTelegramBackend(
            [
                TelegramMessage(message_id=1, sender="Andi", text="Halo"),
                TelegramMessage(message_id=2, sender="Budi", text="Siap"),
            ]
        )
        reader = TelegramGroupReader(backend=backend, chat_id="klinik-dev")

        messages = reader.get_messages_by_sender("Andi")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].sender, "Andi")

    def test_filters_messages_by_keyword(self) -> None:
        backend = InMemoryTelegramBackend(
            [
                TelegramMessage(message_id=1, sender="Andi", text="Sudah bayar"),
                TelegramMessage(message_id=2, sender="Budi", text="Belum"),
            ]
        )
        reader = TelegramGroupReader(backend=backend, chat_id="klinik-dev")

        messages = reader.get_messages_by_keyword("bayar")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].text, "Sudah bayar")

    def test_counts_messages(self) -> None:
        backend = InMemoryTelegramBackend(
            [
                TelegramMessage(message_id=1, sender="Andi", text="A"),
                TelegramMessage(message_id=2, sender="Budi", text="B"),
            ]
        )
        reader = TelegramGroupReader(backend=backend, chat_id="klinik-dev")

        count = reader.count_messages()

        self.assertEqual(count, 2)


if __name__ == "__main__":
    unittest.main()
