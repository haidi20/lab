import threading
import time
import unittest

from fastapi.testclient import TestClient

from modules.inaproc.api.app import create_app
from modules.inaproc.api.gateway_jobs import GatewayJobManager
from modules.inaproc.api.collector import JobState


class FakeStore:
    def create_schema(self):
        pass

    def search(self, **kwargs):
        return []

    def count(self, **kwargs):
        return 0


class SlowSyncService:
    def __init__(self):
        self.calls = []
        self.started = threading.Event()
        self.release = threading.Event()

    def sync(self, scope, params=None, *, force=False):
        self.calls.append((scope, params, force))
        self.started.set()
        self.release.wait(timeout=5)
        return {"scope": scope, "status": "success", "items": 1}


class FakeGatewayStore:
    def create_schema(self):
        pass

    def count_produk(self):
        return 0

    def count_paket(self):
        return 0

    def count_transaksi(self):
        return 0

    def last_run(self, scope=None):
        return None

    def search_produk(self, **kwargs):
        return [], 0

    def search_paket(self, **kwargs):
        return [], 0

    def search_transaksi(self, **kwargs):
        return [], 0


class FakeGatewayClient:
    enabled = True

    def paginate(self, *args, **kwargs):
        return iter(())


class FakeCollector:
    def __init__(self):
        self.job = JobState()


class GatewayJobManagerTest(unittest.TestCase):
    def test_scope_sama_ditolak_saat_running(self):
        service = SlowSyncService()
        manager = GatewayJobManager(service)
        first = manager.start("produk", {}, force=True)
        self.assertTrue(service.started.wait(timeout=2))
        with self.assertRaises(Exception) as ctx:
            manager.start("produk", {}, force=True)
        self.assertEqual(getattr(ctx.exception, "code", ""), "job_aktif")
        service.release.set()
        manager.wait("produk", timeout=3)
        self.assertEqual(first["status"], "running")

    def test_scope_berbeda_boleh_paralel(self):
        service = SlowSyncService()
        manager = GatewayJobManager(service)
        manager.start("produk", {}, force=True)
        self.assertTrue(service.started.wait(timeout=2))
        manager.start("paket", {}, force=True)
        service.release.set()
        manager.wait("produk", timeout=3)
        manager.wait("paket", timeout=3)
        self.assertEqual(len(service.calls), 2)

    def test_status_menyimpan_hasil_akhir(self):
        service = SlowSyncService()
        service.release.set()
        manager = GatewayJobManager(service)
        manager.start("produk", {}, force=True)
        state = manager.wait("produk", timeout=3)
        self.assertEqual(state["status"], "success")
        self.assertEqual(state["items"], 1)

    def test_scope_tidak_dikenal(self):
        manager = GatewayJobManager(SlowSyncService())
        with self.assertRaises(Exception) as ctx:
            manager.start("delete", {}, force=True)
        self.assertEqual(getattr(ctx.exception, "code", ""), "scope_tidak_valid")


class GatewaySyncApiTest(unittest.TestCase):
    def setUp(self):
        self.service = SlowSyncService()
        self.app = create_app(
            store=FakeStore(),
            scraper_factory=lambda: None,
            collector=FakeCollector(),
            gateway_store=FakeGatewayStore(),
            gateway_client=FakeGatewayClient(),
            gateway_sync_service=self.service,
        )
        self.client = TestClient(self.app)

    def tearDown(self):
        self.service.release.set()

    def test_sync_diterima_sebagai_job(self):
        response = self.client.post(
            "/api/gateway/sync/produk", json={"force": True, "params": {}}
        )
        self.assertEqual(response.status_code, 202)
        body = response.json()
        self.assertEqual(body["job"]["scope"], "produk")
        self.assertIn(body["job"]["status"], {"queued", "running"})
        self.assertTrue(self.service.started.wait(timeout=2))

    def test_sync_ganda_scope_sama_409(self):
        first = self.client.post("/api/gateway/sync/produk", json={"force": True})
        self.assertEqual(first.status_code, 202)
        self.assertTrue(self.service.started.wait(timeout=2))
        second = self.client.post("/api/gateway/sync/produk", json={"force": True})
        self.assertEqual(second.status_code, 409)
        self.assertEqual(second.json()["error"], "job_aktif")

    def test_status_job(self):
        self.client.post("/api/gateway/sync/produk", json={"force": True})
        self.assertTrue(self.service.started.wait(timeout=2))
        response = self.client.get("/api/gateway/sync/produk/status")
        self.assertEqual(response.status_code, 200)
        self.assertIn(response.json()["status"], {"queued", "running"})

    def test_status_scope_tidak_dikenal(self):
        response = self.client.get("/api/gateway/sync/delete/status")
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
