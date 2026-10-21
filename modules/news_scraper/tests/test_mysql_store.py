import unittest

from datetime import datetime, timezone, timedelta

from modules.news_scraper import NewsArticle
from modules.news_scraper.mysql_store import NewsMysqlStore


class FakeCursor:
    def __init__(self, store: "FakeConnection") -> None:
        self._store = store

    def execute(self, sql: str, params: tuple = ()) -> None:
        clean = " ".join(sql.split())
        self._store.executed.append((clean, params))
        if clean.startswith("SELECT"):
            self._store.rows = sorted(
                (url, title, source, region, "", published.isoformat(sep=" ") if published else None)
                for url, (title, source, region, published) in self._store.news.items()
            )

    def executemany(self, sql: str, seq: list[tuple]) -> None:
        clean = " ".join(sql.split())
        self._store.executed_many.append((clean, seq))
        if "news_articles" in clean:
            for url, title, source, region, summary, published in seq:
                self._store.news[url] = (title, source, region, published)

    def fetchall(self) -> list[tuple]:
        return self._store.rows


class FakeConnection:
    def __init__(self) -> None:
        self.executed: list[tuple[str, tuple]] = []
        self.executed_many: list[tuple[str, list[tuple]]] = []
        self.news: dict[str, tuple[str, str, str, datetime | None]] = {}
        self.rows: list[tuple] = []
        self.committed = False

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

    def commit(self) -> None:
        self.committed = True


class TestNewsMysqlStore(unittest.TestCase):
    def test_creates_schema_on_init(self) -> None:
        conn = FakeConnection()
        NewsMysqlStore(conn)
        all_sql = " ".join(sql for sql, _ in conn.executed)
        self.assertIn("CREATE TABLE IF NOT EXISTS news_articles", all_sql)

    def test_upsert_articles_no_duplicates_and_updates(self) -> None:
        conn = FakeConnection()
        store = NewsMysqlStore(conn)
        published = datetime(2026, 10, 21, 8, 0, tzinfo=timezone(timedelta(hours=8)))
        article = NewsArticle("Antara Kaltim", "Judul", "https://a/1", published, "Ringkasan", "kaltim")

        store.save_articles([article])
        updated = NewsArticle("Antara Kaltim", "Judul Baru", "https://a/1", published, "Ringkasan", "kaltim")
        store.save_articles([updated])

        self.assertEqual(len(conn.news), 1)
        self.assertEqual(conn.news["https://a/1"][0], "Judul Baru")
        self.assertTrue(conn.committed)

    def test_load_articles_by_date(self) -> None:
        conn = FakeConnection()
        store = NewsMysqlStore(conn)
        published = datetime(2026, 10, 21, 8, 0, tzinfo=timezone(timedelta(hours=8)))
        store.save_articles(
            [NewsArticle("S", "T", "https://a/1", published, "", "kaltim")]
        )

        rows = store.load_articles(datetime(2026, 10, 21).date())

        self.assertEqual(len(rows), 1)
        select_sql = [sql for sql, _ in conn.executed if sql.startswith("SELECT")][0]
        self.assertIn("published_date", select_sql)


if __name__ == "__main__":
    unittest.main()
