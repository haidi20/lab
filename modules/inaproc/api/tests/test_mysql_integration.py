import os
import unittest
from datetime import datetime

from modules.inaproc.api.cache import TkdnMysqlStore
from modules.inaproc.api.config import InaprocDbConfig, load_env_file
from modules.inaproc.api.db import connect_mysql
from modules.inaproc.api.gateway_store import GatewayMysqlStore

def _database_available() -> bool:
    load_env_file()
    try:
        config = InaprocDbConfig.from_env()
        connect_mysql(config, connect_timeout=2).close()
        return True
    except Exception:
        return False

@unittest.skipUnless(_database_available(), "INAPROC MySQL is not configured")
class MysqlIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_env_file()
        cls.config = InaprocDbConfig.from_env()
        cls.tkdn = TkdnMysqlStore(lambda: connect_mysql(cls.config))
        cls.gateway = GatewayMysqlStore(lambda: connect_mysql(cls.config))
        cls.tkdn.create_schema()
        cls.gateway.create_schema()

    def test_schema_idempotent(self):
        self.tkdn.create_schema()
        self.gateway.create_schema()

    def test_upsert_tkdn_lalu_hapus(self):
        number = "900001/SJ-IND.8/E-TKDN/1/2026"
        now = datetime(2026, 1, 1, 0, 0, 0)
        try:
            self.tkdn.upsert_rows(
                number,
                [{"product_type": "Monitor", "brand": "test-brand", "value": 10.5}],
                now,
            )
            self.tkdn.upsert_rows(
                number,
                [{"product_type": "Monitor", "brand": "test-brand", "value": 10.5}],
                now,
            )
            self.tkdn.upsert_check(number, "found", None, now)
            self.assertTrue(self.tkdn.is_final(number))
            rows = self.tkdn.search(number=number)
            self.assertEqual(len(rows), 1)
            self.assertEqual(self.tkdn.count(number=number), 1)
        finally:
            self.tkdn.delete_number(number)
        self.assertIsNone(self.tkdn.get_check(number))

    def test_upsert_produk_idempotent(self):
        row = {
            "kd_produk": "TEST-K1",
            "kode_penyedia": "TEST-P1",
            "nama_produk": "Monitor Test",
            "brand": "Test",
            "harga": 1000,
            "source_url": "https://example.invalid/TEST-K1",
        }
        self.gateway.upsert_produk([row], datetime(2026, 1, 1))
        self.gateway.upsert_produk([row], datetime(2026, 1, 2))
        try:
            rows, total = self.gateway.search_produk(q="Monitor Test")
            self.assertGreaterEqual(total, 1)
            self.assertTrue(any(r["kd_produk"] == "TEST-K1" for r in rows))
        finally:
            self.gateway.delete_produk("TEST-K1")

    def test_audit_run(self):
        run_id = self.gateway.start_run("produk", {"test": True})
        try:
            self.gateway.update_run(run_id, pages=1, total_items=2, status="running")
            self.gateway.finish_run(run_id, "success")
            last = self.gateway.last_run("produk")
            self.assertEqual(last["status"], "success")
        finally:
            self.gateway.delete_run(run_id)

if __name__ == "__main__":
    unittest.main()
