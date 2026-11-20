import unittest
from datetime import datetime

from modules.inaproc.api.gateway_store import (
    GATEWAY_SCHEMA_STATEMENTS,
    GatewayMysqlStore,
)

class FakeCursor:
    def __init__(self, fetchone=None, fetchall=None):
        self.executed = []
        self._fetchone = fetchone
        self._fetchall = fetchall or []
        self.lastrowid = 7

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

class GatewaySchemaTest(unittest.TestCase):
    def test_schema_memiliki_komentar_tabel(self):
        joined = "\n".join(GATEWAY_SCHEMA_STATEMENTS)
        for table in (
            "inaproc_api_sync_runs",
            "inaproc_penyedia",
            "inaproc_produk",
            "inaproc_kategori",
            "inaproc_paket_epurchasing",
            "inaproc_transaksi_epurchasing",
            "inaproc_master_program",
        ):
            self.assertIn(f"CREATE TABLE IF NOT EXISTS {table}", joined)
            self.assertIn(f"ALTER TABLE {table} COMMENT=", joined)
        self.assertNotIn("ADD COLUMN IF NOT EXISTS", joined)

    def test_create_schema_menambah_kolom_yang_belum_ada(self):
        cursor = FakeCursor()
        connection = FakeConnection(cursor)
        store = GatewayMysqlStore(lambda: connection)
        store.create_schema()
        alters = [
            sql
            for sql, _ in cursor.executed
            if "ALTER TABLE" in sql and "ADD COLUMN" in sql
        ]
        self.assertTrue(any("source_updated_at" in sql for sql in alters))
        self.assertTrue(any("retry_status" in sql for sql in alters))

    def test_create_schema_idempotent(self):
        cursor = FakeCursor()
        connection = FakeConnection(cursor)
        store = GatewayMysqlStore(lambda: connection)
        store.create_schema()
        self.assertTrue(connection.committed)
        self.assertTrue(connection.closed)

class GatewayUpsertTest(unittest.TestCase):
    def setUp(self):
        self.cursor = FakeCursor()
        self.connection = FakeConnection(self.cursor)
        self.store = GatewayMysqlStore(lambda: self.connection)
        self.now = datetime(2026, 11, 20, 10, 0, 0)

    def test_upsert_penyedia_idempotent(self):
        row = {
            "kode_penyedia": "P1",
            "nama_penyedia": "PT Contoh",
            "npwp": None,
            "status": "aktif",
            "source_url": "https://penyedia.inaproc.id/p/P1",
        }
        self.store.upsert_penyedia([row], self.now)
        self.store.upsert_penyedia([row], self.now)
        sql, params = self.cursor.executed[-1]
        self.assertIn("INSERT INTO inaproc_penyedia", sql)
        self.assertIn("ON DUPLICATE KEY UPDATE", sql)
        self.assertEqual(params[0], "P1")
        self.assertTrue(self.connection.committed)

    def test_upsert_produk_menyimpan_source_url(self):
        row = {
            "kd_produk": "K1",
            "kode_penyedia": "P1",
            "nama_produk": "Monitor 24",
            "kategori": "Monitor",
            "brand": "Acer",
            "harga": 1500000,
            "satuan": "Unit",
            "source_url": "https://katalog.inaproc.id/produk/K1",
        }
        self.store.upsert_produk([row], self.now)
        sql, params = self.cursor.executed[-1]
        self.assertIn("source_url", sql)
        self.assertIn("source_updated_at", sql)
        self.assertIn("https://katalog.inaproc.id/produk/K1", params)

    def test_upsert_kategori(self):
        self.store.upsert_kategori(
            [{"kode_kategori": "C1", "nama_kategori": "Komputer", "level": 1}],
            self.now,
        )
        sql = self.cursor.executed[-1][0]
        self.assertIn("INSERT INTO inaproc_kategori", sql)

    def test_upsert_paket_dan_transaksi(self):
        self.store.upsert_paket(
            [
                {
                    "kode_paket": "PK1",
                    "nama_paket": "Paket Monitor",
                    "tahun": 2026,
                    "kode_klpd": "K1",
                }
            ],
            self.now,
        )
        self.store.upsert_transaksi(
            [
                {
                    "order_id": "O1",
                    "kd_produk": "K1",
                    "kode_penyedia": "P1",
                    "jumlah": 2,
                    "total": 3000000,
                    "tahun": 2026,
                }
            ],
            self.now,
        )
        sqls = "\n".join(sql for sql, _ in self.cursor.executed)
        self.assertIn("INSERT INTO inaproc_paket_epurchasing", sqls)
        self.assertIn("INSERT INTO inaproc_transaksi_epurchasing", sqls)

    def test_upsert_program(self):
        self.store.upsert_program(
            [{"kode_program": "PR1", "nama_program": "Program A", "tahun": 2026}],
            self.now,
        )
        self.assertIn("INSERT INTO inaproc_master_program", self.cursor.executed[-1][0])

    def test_batch_kosong_tidak_query(self):
        self.store.upsert_produk([], self.now)
        self.assertEqual(self.cursor.executed, [])

class GatewaySyncRunTest(unittest.TestCase):
    def setUp(self):
        self.cursor = FakeCursor(fetchone={"id": 7})
        self.connection = FakeConnection(self.cursor)
        self.store = GatewayMysqlStore(lambda: self.connection)

    def test_start_run_insert_running(self):
        run_id = self.store.start_run("produk", {"kode_penyedia": "P1"})
        sql, params = self.cursor.executed[-1]
        self.assertIn("INSERT INTO inaproc_api_sync_runs", sql)
        self.assertIn("'running'", sql)
        self.assertIn("produk", params)
        self.assertEqual(run_id, 7)

    def test_update_progress(self):
        self.store.update_run(7, cursor="c2", pages=2, total_items=50, status="running")
        sql, params = self.cursor.executed[-1]
        self.assertIn("UPDATE inaproc_api_sync_runs", sql)
        self.assertIn("c2", params)

    def test_finish_success(self):
        self.store.finish_run(7, "success")
        sql, params = self.cursor.executed[-1]
        self.assertIn("status=%s", sql)
        self.assertIn("success", params)

    def test_finish_failed_menyimpan_error(self):
        self.store.finish_run(7, "failed", error_code="TOKEN_EXPIRED", error_msg="expired")
        sql, params = self.cursor.executed[-1]
        self.assertIn("TOKEN_EXPIRED", params)

    def test_last_run(self):
        cursor = FakeCursor(fetchone={"id": 7, "status": "success"})
        store = GatewayMysqlStore(lambda: FakeConnection(cursor))
        self.assertEqual(store.last_run("produk")["status"], "success")

class GatewaySearchTest(unittest.TestCase):
    def test_search_produk_pagination(self):
        cursor = FakeCursor(fetchall=[{"kd_produk": "K1"}], fetchone={"total": 1})
        store = GatewayMysqlStore(lambda: FakeConnection(cursor))
        rows, total = store.search_produk(q="monitor", page=2, per_page=10)
        self.assertEqual(rows[0]["kd_produk"], "K1")
        self.assertEqual(total, 1)
        sql, params = cursor.executed[-1]
        self.assertIn("LIMIT %s OFFSET %s", sql)
        self.assertEqual(tuple(params[-2:]), (10, 10))

    def test_search_produk_sort_whitelist(self):
        store = GatewayMysqlStore(lambda: FakeConnection(FakeCursor()))
        with self.assertRaises(ValueError):
            store.search_produk(sort="drop table")

    def test_search_paket_filter_dan_pagination(self):
        cursor = FakeCursor(fetchall=[{"kode_paket": "PK1"}], fetchone={"total": 1})
        store = GatewayMysqlStore(lambda: FakeConnection(cursor))
        rows, total = store.search_paket(
            q="monitor",
            tahun=2026,
            kode_klpd="K1",
            page=2,
            per_page=10,
        )
        self.assertEqual(rows[0]["kode_paket"], "PK1")
        self.assertEqual(total, 1)
        count_sql, count_params = cursor.executed[0]
        list_sql, list_params = cursor.executed[1]
        self.assertIn("FROM inaproc_paket_epurchasing", count_sql)
        self.assertIn("tahun = %s", count_sql)
        self.assertIn("kode_klpd = %s", count_sql)
        self.assertEqual(tuple(count_params), ("%monitor%", "%monitor%", "%monitor%", 2026, "K1"))
        self.assertIn("LIMIT %s OFFSET %s", list_sql)
        self.assertEqual(tuple(list_params[-2:]), (10, 10))

    def test_search_transaksi_filter_dan_sort(self):
        cursor = FakeCursor(fetchall=[{"order_id": "O1"}], fetchone={"total": 1})
        store = GatewayMysqlStore(lambda: FakeConnection(cursor))
        rows, total = store.search_transaksi(
            q="laptop",
            tahun=2026,
            kd_produk="K1",
            sort="total",
            order="desc",
        )
        self.assertEqual(rows[0]["order_id"], "O1")
        self.assertEqual(total, 1)
        count_sql, count_params = cursor.executed[0]
        list_sql, _ = cursor.executed[1]
        self.assertIn("FROM inaproc_transaksi_epurchasing", count_sql)
        self.assertIn("kd_produk = %s", count_sql)
        self.assertEqual(tuple(count_params), ("%laptop%", "%laptop%", "%laptop%", 2026, "K1"))
        self.assertIn("ORDER BY total DESC", list_sql)

    def test_search_transaksi_sort_whitelist(self):
        store = GatewayMysqlStore(lambda: FakeConnection(FakeCursor()))
        with self.assertRaises(ValueError):
            store.search_transaksi(sort="drop table")

if __name__ == "__main__":
    unittest.main()
