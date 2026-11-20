import unittest
from datetime import datetime
from unittest.mock import MagicMock

from modules.inaproc.api.cache import TkdnMysqlStore, row_hash


class FakeCursor:
    def __init__(self, fetchone=None, fetchall=None):
        self.executed = []
        self._fetchone = fetchone
        self._fetchall = fetchall or []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        return self._fetchone

    def fetchall(self):
        return self._fetchall


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def sample_row(**overrides):
    row = {
        "product_type": "Monitor",
        "brand": "acer",
        "type": "V",
        "description": "23.8 Inchi",
        "standard": "-",
        "value": 33.39,
        "hs": None,
        "specification_id": None,
    }
    row.update(overrides)
    return row


class RowHashTest(unittest.TestCase):
    def test_row_hash_stabil(self):
        self.assertEqual(row_hash("n", sample_row()), row_hash("n", sample_row()))

    def test_none_dan_kosong_setara(self):
        self.assertEqual(
            row_hash("n", sample_row(standard=None)),
            row_hash("n", sample_row(standard="")),
        )


class CacheWriteTest(unittest.TestCase):
    def setUp(self):
        self.cursor = FakeCursor()
        self.connection = FakeConnection(self.cursor)
        self.store = TkdnMysqlStore(lambda: self.connection)

    def test_simpan_dan_baca(self):
        self.store.upsert_rows("11469/SJ-IND.8/E-TKDN/7/2025", [sample_row()], datetime(2025, 7, 1))
        sql, params = self.cursor.executed[-1]
        self.assertIn("INSERT INTO tkdn_rows", sql)
        self.assertIn("ON DUPLICATE KEY UPDATE", sql)
        self.assertEqual(params[0], "11469/SJ-IND.8/E-TKDN/7/2025")
        self.assertTrue(self.connection.committed)
        self.assertTrue(self.connection.closed)

    def test_upsert_tanpa_duplikat_memakai_row_hash(self):
        self.store.upsert_rows("n", [sample_row()], datetime(2025, 7, 1))
        self.store.upsert_rows("n", [sample_row()], datetime(2025, 7, 2))
        self.assertEqual(len(self.cursor.executed), 2)
        self.assertEqual(
            self.cursor.executed[0][1][-1],
            self.cursor.executed[1][1][-1],
        )

    def test_upsert_perbarui_nilai(self):
        self.store.upsert_rows("n", [sample_row(value=33.39)], datetime(2025, 7, 1))
        sql = self.cursor.executed[-1][0]
        self.assertIn("value=VALUES(value)", sql.replace(" ", ""))
        self.assertIn("fetched_at=VALUES(fetched_at)", sql.replace(" ", ""))

    def test_event_empty_hapus_baris(self):
        self.store.delete_rows_for_number("n")
        sql, params = self.cursor.executed[-1]
        self.assertIn("DELETE FROM tkdn_rows", sql)
        self.assertEqual(params, ("n",))
        self.assertTrue(self.connection.committed)

    def test_upsert_check(self):
        self.store.upsert_check("n", "found", None, datetime(2025, 7, 1))
        sql, params = self.cursor.executed[-1]
        self.assertIn("INSERT INTO tkdn_checks", sql)
        self.assertEqual(params[0], "n")
        self.assertEqual(params[1], "found")

    def test_delete_number_satu_transaksi(self):
        self.store.delete_number("n")
        sqls = [sql for sql, _ in self.cursor.executed]
        self.assertTrue(any("DELETE FROM tkdn_rows" in s for s in sqls))
        self.assertTrue(any("DELETE FROM tkdn_checks" in s for s in sqls))
        self.assertTrue(self.connection.committed)

    def test_koneksi_ditutup_walau_query_gagal(self):
        self.cursor.execute = MagicMock(side_effect=RuntimeError("boom"))
        with self.assertRaises(RuntimeError):
            self.store.upsert_check("n", "error", "x", datetime(2025, 7, 1))
        self.assertTrue(self.connection.closed)
        self.assertTrue(self.connection.rolled_back)


class CacheReadTest(unittest.TestCase):
    def test_get_check(self):
        cursor = FakeCursor(fetchone={"number": "n", "status": "found"})
        store = TkdnMysqlStore(lambda: FakeConnection(cursor))
        self.assertEqual(store.get_check("n")["status"], "found")

    def test_get_checks(self):
        cursor = FakeCursor(fetchall=[{"number": "a", "status": "found"}])
        store = TkdnMysqlStore(lambda: FakeConnection(cursor))
        result = store.get_checks(["a", "b"])
        self.assertEqual(len(result), 1)
        self.assertIn("IN", cursor.executed[-1][0])

    def test_status_error_dianggap_belum_final(self):
        cursor = FakeCursor(fetchone={"number": "n", "status": "error"})
        store = TkdnMysqlStore(lambda: FakeConnection(cursor))
        self.assertFalse(store.is_final("n"))

    def test_status_found_tanpa_baris_tidak_konsisten(self):
        cursor = FakeCursor(fetchone={"number": "n", "status": "found", "row_count": 0})
        store = TkdnMysqlStore(lambda: FakeConnection(cursor))
        self.assertFalse(store.is_final("n"))

    def test_search_filter_brand_case_insensitive(self):
        cursor = FakeCursor(fetchall=[])
        store = TkdnMysqlStore(lambda: FakeConnection(cursor))
        store.search(q="", brand="Acer", min_value=None, page=1, per_page=50)
        sql, params = cursor.executed[-1]
        self.assertIn("LOWER(brand) = LOWER(%s)", sql)
        self.assertIn("Acer", params)

    def test_exact_number_filter_tanpa_wildcard(self):
        cursor = FakeCursor(fetchall=[])
        store = TkdnMysqlStore(lambda: FakeConnection(cursor))
        store.search(number="11469/SJ-IND.8/E-TKDN/7/2025")
        sql, params = cursor.executed[-1]
        self.assertIn("number = %s", sql)
        self.assertEqual(params[0], "11469/SJ-IND.8/E-TKDN/7/2025")

    def test_count_total_dengan_filter(self):
        cursor = FakeCursor(fetchone={"total": 7})
        store = TkdnMysqlStore(lambda: FakeConnection(cursor))
        self.assertEqual(store.count(q="acer", min_value=30), 7)
        sql, params = cursor.executed[-1]
        self.assertIn("SELECT COUNT(*)", sql)
        self.assertIn(30, params)

    def test_filter_nilai_minimum(self):
        cursor = FakeCursor(fetchall=[])
        store = TkdnMysqlStore(lambda: FakeConnection(cursor))
        store.search(q="", brand=None, min_value=30, page=1, per_page=50)
        sql, params = cursor.executed[-1]
        self.assertIn("value >= %s", sql)
        self.assertIn(30, params)

    def test_sort_diluar_whitelist_ditolak(self):
        cursor = FakeCursor(fetchall=[])
        store = TkdnMysqlStore(lambda: FakeConnection(cursor))
        with self.assertRaises(ValueError):
            store.search(q="", brand=None, min_value=None, page=1, per_page=50, sort="drop table")

    def test_pagination_limit_offset(self):
        cursor = FakeCursor(fetchall=[])
        store = TkdnMysqlStore(lambda: FakeConnection(cursor))
        store.search(q="", brand=None, min_value=None, page=3, per_page=50)
        sql, params = cursor.executed[-1]
        self.assertIn("LIMIT %s OFFSET %s", sql)
        self.assertEqual(tuple(params[-2:]), (50, 100))


if __name__ == "__main__":
    unittest.main()
