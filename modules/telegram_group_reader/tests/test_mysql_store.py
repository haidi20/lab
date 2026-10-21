import unittest

from modules.telegram_group_reader import (
    MysqlMessageStore,
    TelegramGroupInfo,
    TelegramMessage,
)


class FakeCursor:
    def __init__(self, store: "FakeConnection") -> None:
        self._store = store

    def execute(self, sql: str, params: tuple = ()) -> None:
        self._store.executed.append((sql.strip(), params))

    def executemany(self, sql: str, seq: list[tuple]) -> None:
        self._store.executed_many.append((sql.strip(), seq))

    def fetchall(self) -> list[tuple]:
        return self._store.rows


class FakeConnection:
    def __init__(self, rows: list[tuple] | None = None) -> None:
        self.executed: list[tuple[str, tuple]] = []
        self.executed_many: list[tuple[str, list[tuple]]] = []
        self.committed = False
        self.rows = rows or []

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

    def commit(self) -> None:
        self.committed = True


class TestMysqlMessageStore(unittest.TestCase):
    def test_creates_schema_on_init(self) -> None:
        connection = FakeConnection()

        MysqlMessageStore(connection)

        all_sql = " ".join(sql for sql, _ in connection.executed)
        self.assertIn("CREATE TABLE IF NOT EXISTS telegram_groups", all_sql)
        self.assertIn("CREATE TABLE IF NOT EXISTS telegram_messages", all_sql)

    def test_saves_group(self) -> None:
        connection = FakeConnection()
        store = MysqlMessageStore(connection)

        store.save_group(
            TelegramGroupInfo(group_id="-1001", title="Klinik Dev", group_type="group")
        )

        sql, params = connection.executed_many[0]
        self.assertIn("INSERT", sql)
        self.assertIn("telegram_groups", sql)
        self.assertEqual(params, [("-1001", "Klinik Dev", "group")])
        self.assertTrue(connection.committed)

    def test_saves_messages_with_group_title(self) -> None:
        connection = FakeConnection()
        store = MysqlMessageStore(connection)
        messages = [
            TelegramMessage(message_id=1, sender="Andi", text="Halo"),
            TelegramMessage(message_id=2, sender="Budi", text="Siap"),
        ]

        store.save_messages("Klinik Dev", messages)

        sql, params = connection.executed_many[0]
        self.assertIn("INSERT", sql)
        self.assertIn("telegram_messages", sql)
        self.assertEqual(
            params,
            [
                ("Klinik Dev", 1, "Andi", "Halo"),
                ("Klinik Dev", 2, "Budi", "Siap"),
            ],
        )
        self.assertTrue(connection.committed)

    def test_loads_messages_by_group_title(self) -> None:
        connection = FakeConnection(
            [(1, "Andi", "Halo"), (2, "Budi", "Siap")]
        )
        store = MysqlMessageStore(connection)

        messages = store.load_messages("Klinik Dev")

        sql, params = connection.executed[-1]
        self.assertIn("SELECT", sql)
        self.assertIn("telegram_messages", sql)
        self.assertEqual(params, ("Klinik Dev",))
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].sender, "Andi")
        self.assertEqual(messages[1].text, "Siap")

    def test_saves_many_groups_in_bulk(self) -> None:
        connection = FakeConnection()
        store = MysqlMessageStore(connection)
        groups = [
            TelegramGroupInfo(group_id="-1001", title="Group A", group_type="group"),
            TelegramGroupInfo(group_id="-1002", title="Channel B", group_type="channel"),
        ]

        store.save_groups(groups)

        sql, params = connection.executed_many[0]
        self.assertIn("telegram_groups", sql)
        self.assertEqual(len(params), 2)


class UpsertFakeCursor:
    def __init__(self, store: "UpsertFakeConnection") -> None:
        self._store = store

    def executemany(self, sql: str, seq: list[tuple]) -> None:
        clean = " ".join(sql.split())
        if "telegram_groups" in clean:
            for group_id, title, group_type in seq:
                self._store.groups[group_id] = (title, group_type)
        elif "telegram_messages" in clean:
            for group_title, message_id, sender, text in seq:
                self._store.messages[(group_title, message_id)] = (sender, text)

    def execute(self, sql: str, params: tuple = ()) -> None:
        clean = " ".join(sql.split())
        if clean.startswith("SELECT"):
            group_title = params[0]
            self._store.rows = sorted(
                (mid, sender, text)
                for (title, mid), (sender, text) in self._store.messages.items()
                if title == group_title
            )

    def fetchall(self) -> list[tuple]:
        return self._store.rows


class UpsertFakeConnection:
    def __init__(self) -> None:
        self.groups: dict[str, tuple[str, str]] = {}
        self.messages: dict[tuple[str, int], tuple[str, str]] = {}
        self.rows: list[tuple] = []
        self.committed = False

    def cursor(self) -> UpsertFakeCursor:
        return UpsertFakeCursor(self)

    def commit(self) -> None:
        self.committed = True


class TestUpsertSemantics(unittest.TestCase):
    def test_upsert_group_updates_title_without_duplicates(self) -> None:
        db = UpsertFakeConnection()
        store = MysqlMessageStore(db)

        store.save_group(TelegramGroupInfo(group_id="-1001", title="Old", group_type="group"))
        store.save_group(TelegramGroupInfo(group_id="-1001", title="New", group_type="group"))

        self.assertEqual(len(db.groups), 1)
        self.assertEqual(db.groups["-1001"], ("New", "group"))

    def test_upsert_message_updates_text_without_duplicates(self) -> None:
        db = UpsertFakeConnection()
        store = MysqlMessageStore(db)

        store.save_messages("G", [TelegramMessage(message_id=1, sender="Andi", text="v1")])
        store.save_messages("G", [TelegramMessage(message_id=1, sender="Andi", text="v2")])

        self.assertEqual(len(db.messages), 1)
        self.assertEqual(db.messages[("G", 1)], ("Andi", "v2"))


if __name__ == "__main__":
    unittest.main()
