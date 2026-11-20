import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from modules.inaproc.api.app import create_app
from modules.inaproc.api.collector import JobState

class FakeTkdnStore:
    def create_schema(self):
        pass

    def search(self, **kwargs):
        return []

    def count(self, **kwargs):
        return 0

    def get_check(self, number):
        return None

    def get_checks(self, numbers):
        return []

    def is_final(self, number):
        return False

class FakeGatewayStore:
    def __init__(self):
        self.synced = []

    def create_schema(self):
        pass

    def count_produk(self):
        return 2

    def count_paket(self):
        return 3

    def count_transaksi(self):
        return 4

    def search_produk(self, **kwargs):
        return (
            [
                {
                    "kd_produk": "K1",
                    "nama_produk": "Monitor 24",
                    "brand": "Acer",
                    "harga": 1500000,
                    "source_url": "https://katalog.inaproc.id/produk/K1",
                }
            ],
            1,
        )

    def search_paket(self, **kwargs):
        return (
            [
                {
                    "kode_paket": "PK1",
                    "nama_paket": "Paket Monitor",
                    "tahun": 2026,
                    "kode_klpd": "K1",
                    "total_nilai": 2500000,
                    "source_url": "https://katalog.inaproc.id/paket/PK1",
                }
            ],
            1,
        )

    def search_transaksi(self, **kwargs):
        return (
            [
                {
                    "order_id": "O1",
                    "kd_produk": "K1",
                    "nama_produk": "Monitor 24",
                    "jumlah": 2,
                    "total": 3000000,
                    "tahun": 2026,
                }
            ],
            1,
        )

    def last_run(self, scope=None):
        return {"id": 1, "scope": scope, "status": "success"}

    def start_run(self, scope, params=None):
        return 1

    def update_run(self, run_id, **kwargs):
        pass

    def finish_run(self, run_id, status, **kwargs):
        pass

    def upsert_produk(self, rows, now):
        self.synced.extend(rows)
        return len(rows)

    def upsert_paket(self, rows, now):
        self.synced.extend(rows)
        return len(rows)

class FakeGatewayClient:
    def __init__(self, enabled=True):
        self.enabled = enabled

    def paginate(self, path, **kwargs):
        if path == "/api/v1/ekatalog/paket-e-purchasing":
            yield [
                {
                    "kode_paket": "PK1",
                    "nama_paket": "Paket Monitor",
                    "tahun": 2026,
                    "kode_klpd": "K1",
                }
            ]
            return
        yield [
            {
                "kd_produk": "K1",
                "nama_produk": "Monitor 24",
                "kode_penyedia": "P1",
                "url": "https://katalog.inaproc.id/produk/K1",
            }
        ]

class FakeCollector:
    def __init__(self):
        self.job = JobState()

class GatewayApiTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.session = Path(self.tmp.name) / "storageState.json"
        self.gateway_store = FakeGatewayStore()
        self.gateway_client = FakeGatewayClient()
        self.app = create_app(
            store=FakeTkdnStore(),
            scraper_factory=lambda: None,
            session_path=self.session,
            collector=FakeCollector(),
            gateway_store=self.gateway_store,
            gateway_client=self.gateway_client,
        )
        self.client = TestClient(self.app)

    def tearDown(self):
        self.tmp.cleanup()

    def test_status_gateway(self):
        response = self.client.get("/api/gateway/status")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["enabled"])
        self.assertEqual(body["produk_count"], 2)
        self.assertEqual(body["paket_count"], 3)
        self.assertEqual(body["transaksi_count"], 4)
        self.assertNotIn("token", body)

    def test_status_gateway_tetap_200_saat_cache_belum_siap(self):
        def boom():
            raise RuntimeError("cache table missing")

        self.gateway_store.count_produk = boom
        response = self.client.get("/api/gateway/status")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["produk_count"], 0)

    def test_cari_produk_dari_db(self):
        response = self.client.get("/api/gateway/produk", params={"q": "monitor"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["items"][0]["kd_produk"], "K1")
        self.assertEqual(body["total"], 1)
        self.assertEqual(
            body["items"][0]["source_url"], "https://katalog.inaproc.id/produk/K1"
        )

    def test_cari_paket_epurchasing_dari_db(self):
        response = self.client.get("/api/gateway/epurchasing", params={"q": "monitor"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["items"][0]["kode_paket"], "PK1")
        self.assertEqual(body["total"], 1)
        self.assertEqual(
            body["items"][0]["source_url"], "https://katalog.inaproc.id/paket/PK1"
        )

    def test_cari_transaksi_epurchasing_dari_db(self):
        response = self.client.get(
            "/api/gateway/epurchasing",
            params={"kind": "transaksi", "q": "monitor", "tahun": 2026},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["items"][0]["order_id"], "O1")
        self.assertEqual(body["total"], 1)

    def test_cari_epurchasing_kind_invalid(self):
        response = self.client.get(
            "/api/gateway/epurchasing", params={"kind": "delete"}
        )
        self.assertEqual(response.status_code, 422)

    def test_export_produk_csv(self):
        response = self.client.get(
            "/api/gateway/export", params={"kind": "produk", "format": "csv"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response.headers["content-type"])
        self.assertIn("kd_produk", response.text)
        self.assertIn("K1", response.text)

    def test_export_paket_json(self):
        response = self.client.get(
            "/api/gateway/export", params={"kind": "paket", "format": "json"}
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body[0]["kode_paket"], "PK1")
        self.assertNotIn("token", response.text.lower())

    def test_export_transaksi_json(self):
        response = self.client.get(
            "/api/gateway/export",
            params={"kind": "transaksi", "format": "json", "tahun": 2026},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["order_id"], "O1")

    def test_export_kind_invalid(self):
        response = self.client.get(
            "/api/gateway/export", params={"kind": "delete", "format": "csv"}
        )
        self.assertEqual(response.status_code, 422)

    def test_export_format_invalid(self):
        response = self.client.get(
            "/api/gateway/export", params={"kind": "produk", "format": "xml"}
        )
        self.assertEqual(response.status_code, 422)

    def test_sync_produk(self):
        response = self.client.post(
            "/api/gateway/sync/produk", json={"force": True, "params": {}}
        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()["job"]["scope"], "produk")
        state = self.app.state.gateway_jobs.wait("produk", timeout=3)
        self.assertEqual(state["status"], "success")
        self.assertEqual(len(self.gateway_store.synced), 1)

    def test_sync_scope_invalid(self):
        response = self.client.post("/api/gateway/sync/delete", json={"force": True})
        self.assertEqual(response.status_code, 422)

    def test_sync_paket_scope(self):
        response = self.client.post(
            "/api/gateway/sync/paket", json={"force": True, "params": {"tahun": 2026}}
        )
        self.assertEqual(response.status_code, 202)
        state = self.app.state.gateway_jobs.wait("paket", timeout=3)
        self.assertEqual(state["status"], "success")
        self.assertEqual(state["scope"], "paket")

    def test_status_sync(self):
        self.client.post("/api/gateway/sync/produk", json={"force": True})
        self.app.state.gateway_jobs.wait("produk", timeout=3)
        response = self.client.get("/api/gateway/sync/produk/status")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")

    def test_gateway_disabled(self):
        app = create_app(
            store=FakeTkdnStore(),
            scraper_factory=lambda: None,
            session_path=self.session,
            collector=FakeCollector(),
            gateway_store=self.gateway_store,
            gateway_client=FakeGatewayClient(enabled=False),
        )
        response = TestClient(app).post(
            "/api/gateway/sync/produk", json={"force": True}
        )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"], "gateway_disabled")

if __name__ == "__main__":
    unittest.main()
