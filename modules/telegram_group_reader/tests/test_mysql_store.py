import unittest
from datetime import datetime, timezone, timedelta

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

    def fetchone(self) -> tuple[int]:
        return (1,)

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
        self.assertIn("created DATETIME NULL", all_sql)

    def test_migrates_existing_table_with_created_column(self) -> None:
        connection = MigrationFakeConnection(existing_column_count=0)

        MysqlMessageStore(connection)

        self.assertIn(
            "ALTER TABLE telegram_messages ADD COLUMN created DATETIME NULL",
            connection.executed,
        )

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
        created = datetime(2026, 11, 3, 10, 15, tzinfo=timezone(timedelta(hours=8)))
        messages = [
            TelegramMessage(message_id=1, sender="Andi", text="Halo", date=created),
            TelegramMessage(message_id=2, sender="Budi", text="Siap"),
        ]

        store.save_messages("Klinik Dev", messages)

        sql, params = connection.executed_many[0]
        self.assertIn("INSERT", sql)
        self.assertIn("telegram_messages", sql)
        self.assertIn(
            "(group_title, message_id, sender, text, created)",
            sql,
        )
        self.assertEqual(
            params,
            [
                ("Klinik Dev", 1, "Andi", "Halo", created),
                ("Klinik Dev", 2, "Budi", "Siap", None),
            ],
        )
        self.assertTrue(connection.committed)

    def test_loads_messages_with_created_date(self) -> None:
        created = datetime(2026, 11, 3, 10, 15)
        connection = FakeConnection([(1, "Andi", "Halo", created)])
        store = MysqlMessageStore(connection)

        messages = store.load_messages("Klinik Dev")

        self.assertEqual(messages[0].date, created)

    def test_loads_messages_by_group_title(self) -> None:
        connection = FakeConnection(
            [(1, "Andi", "Halo", None), (2, "Budi", "Siap", None)]
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


class MigrationFakeCursor:
    def __init__(self, store: "MigrationFakeConnection") -> None:
        self._store = store

    def execute(self, sql: str, params: tuple = ()) -> None:
        self._store.executed.append(" ".join(sql.split()))

    def fetchone(self) -> tuple[int]:
        return (self._store.existing_column_count,)

class MigrationFakeConnection:
    def __init__(self, existing_column_count: int) -> None:
        self.executed: list[str] = []
        self.existing_column_count = existing_column_count

    def cursor(self) -> MigrationFakeCursor:
        return MigrationFakeCursor(self)

    def commit(self) -> None:
        pass

class UpsertFakeCursor:
    def __init__(self, store: "UpsertFakeConnection") -> None:
        self._store = store

    def executemany(self, sql: str, seq: list[tuple]) -> None:
        clean = " ".join(sql.split())
        if "telegram_groups" in clean:
            for group_id, title, group_type in seq:
                self._store.groups[group_id] = (title, group_type)
        elif "telegram_messages" in clean:
            for group_title, message_id, sender, text, created in seq:
                existing = self._store.messages.get((group_title, message_id))
                if existing is None:
                    self._store.messages[(group_title, message_id)] = (sender, text, created)
                else:
                    self._store.messages[(group_title, message_id)] = (sender, text, existing[2])

    def execute(self, sql: str, params: tuple = ()) -> None:
        clean = " ".join(sql.split())
        if clean.startswith("SELECT") and params:
            group_title = params[0]
            self._store.rows = sorted(
                (mid, sender, text, created)
                for (title, mid), (sender, text, created) in self._store.messages.items()
                if title == group_title
            )

    def fetchone(self) -> tuple[int]:
        return (1,)

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

    def test_upsert_message_updates_text_and_preserves_created(self) -> None:
        db = UpsertFakeConnection()
        store = MysqlMessageStore(db)
        created = datetime(2026, 11, 3, 10, 15)

        store.save_messages("G", [TelegramMessage(message_id=1, sender="Andi", text="v1", date=created)])
        store.save_messages("G", [TelegramMessage(message_id=1, sender="Andi", text="v2")])

        self.assertEqual(db.messages[("G", 1)], ("Andi", "v2", created))


if __name__ == "__main__":
    unittest.main()
