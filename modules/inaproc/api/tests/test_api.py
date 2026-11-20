import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from modules.inaproc.api.app import create_app
from modules.inaproc.api.auth import AuthError
from modules.inaproc.api.collector import JobState
from modules.inaproc.api.scraper import ScrapeResult

SAMPLE = "11469/SJ-IND.8/E-TKDN/7/2025"
SESSION_STATE = {
    "cookies": [
        {
            "name": "session",
            "value": "dummy",
            "domain": ".inaproc.id",
            "path": "/",
        }
    ],
    "origins": [],
}



def _write_session(path):
    import json

    Path(path).write_text(json.dumps(SESSION_STATE), encoding="utf-8")
    return {"connected": True, "session_path": str(path)}

class FakeStore:
    def __init__(self):
        self.last_search = {}

    def __init__(self):
        self.checks = {}
        self.rows = []
        self.deleted = []

    def create_schema(self):
        pass

    def get_check(self, number):
        return self.checks.get(number)

    def get_checks(self, numbers):
        return [self.checks[n] for n in numbers if n in self.checks]

    def is_final(self, number):
        check = self.checks.get(number)
        return bool(check and check.get("status") in {"found", "empty"})

    def upsert_rows(self, number, rows, fetched_at):
        for row in rows:
            self.rows.append({**row, "number": number})

    def delete_rows_for_number(self, number):
        self.deleted.append(number)
        self.rows = [r for r in self.rows if r["number"] != number]

    def upsert_check(self, number, status, error_msg, checked_at):
        self.checks[number] = {"number": number, "status": status, "error_msg": error_msg}

    def delete_number(self, number):
        self.checks.pop(number, None)
        self.delete_rows_for_number(number)

    def search(self, **kwargs):
        self.last_search = kwargs
        return self.rows

    def count(self, **kwargs):
        return len(self.rows)


class FakeScraper:
    def __init__(self, result=None, error=None):
        self.result = result or ScrapeResult(status="found", rows=[{"brand": "acer"}])
        self.error = error
        self.calls = []

    def fetch(self, number):
        self.calls.append(str(number))
        if self.error is not None:
            raise self.error
        return self.result


class FakeCollector:
    def __init__(self):
        self.job = JobState()
        self.cancelled = False

    def collect(self, template, start, end):
        self.job = JobState(total=end - start + 1, empty=end - start + 1, status="done")
        return self.job

    def cancel(self):
        self.cancelled = True

class FakeGatewayStore:
    def create_schema(self):
        pass

    def count_produk(self):
        return 0

    def last_run(self, scope=None):
        return None

    def search_produk(self, **kwargs):
        return [], 0

class FakeGatewayClient:
    enabled = False

    def paginate(self, *args, **kwargs):
        return iter(())


class ApiTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.session = Path(self.tmp.name) / "storageState.json"
        self.store = FakeStore()
        self.scraper = FakeScraper()
        self.collector = FakeCollector()
        self.app = create_app(
            store=self.store,
            scraper_factory=lambda: self.scraper,
            session_path=self.session,
            collector=self.collector,
            connect_inaproc_fn=lambda email, password, path: _write_session(path),
            gateway_store=FakeGatewayStore(),
            gateway_client=FakeGatewayClient(),
        )
        self.client = TestClient(self.app)

    def tearDown(self):
        self.tmp.cleanup()

    def write_session(self):
        import json

        self.session.write_text(json.dumps(SESSION_STATE), encoding="utf-8")

    def test_session_tanpa_file(self):
        response = self.client.get("/api/session")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["configured"])

    def test_connect_inaproc_sukses(self):
        response = self.client.post(
            "/api/login", json={"email": "user@example.com", "password": "secret"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["connected"])

    def test_connect_inaproc_kredensial_salah(self):
        app = create_app(
            store=self.store,
            scraper_factory=lambda: self.scraper,
            session_path=self.session,
            collector=self.collector,
            connect_inaproc_fn=lambda *args: (_ for _ in ()).throw(AuthError("bad")),
            gateway_store=FakeGatewayStore(),
            gateway_client=FakeGatewayClient(),
        )
        client = TestClient(app)
        response = client.post(
            "/api/login", json={"email": "user@example.com", "password": "bad"}
        )
        self.assertEqual(response.status_code, 401)

    def test_connect_inaproc_email_tidak_terdaftar(self):
        app = create_app(
            store=self.store,
            scraper_factory=lambda: self.scraper,
            session_path=self.session,
            collector=self.collector,
            connect_inaproc_fn=lambda *args: (_ for _ in ()).throw(
                AuthError("INAPROC email is not registered")
            ),
            gateway_store=FakeGatewayStore(),
            gateway_client=FakeGatewayClient(),
        )
        client = TestClient(app)

        response = client.post(
            "/api/login", json={"email": "unknown@example.com", "password": "secret"}
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "kredensial_salah")
        self.assertIn("not registered", response.json()["message"].lower())
        self.assertFalse(self.session.exists())

    def test_connect_inaproc_butuh_otp(self):
        app = create_app(
            store=self.store,
            scraper_factory=lambda: self.scraper,
            session_path=self.session,
            collector=self.collector,
            connect_inaproc_fn=lambda *args: (_ for _ in ()).throw(
                AuthError("INAPROC requires OTP")
            ),
            gateway_store=FakeGatewayStore(),
            gateway_client=FakeGatewayClient(),
        )
        client = TestClient(app)
        response = client.post(
            "/api/login", json={"email": "user@example.com", "password": "secret"}
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"], "butuh_interaksi")

    def test_logout_hapus_state(self):
        self.session.write_text("{}", encoding="utf-8")
        response = self.client.post("/api/logout")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.session.exists())

    def test_lookup_dari_db(self):
        self.store.checks[SAMPLE] = {"number": SAMPLE, "status": "found"}
        self.store.rows = [{"number": SAMPLE, "brand": "acer"}]
        response = self.client.post("/api/lookup", json={"number": SAMPLE})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["source"], "db")
        self.assertEqual(self.scraper.calls, [])

    def test_lookup_scrape_bila_belum_ada(self):
        self.write_session()
        response = self.client.post("/api/lookup", json={"number": SAMPLE})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["source"], "scrape")
        self.assertEqual(len(self.scraper.calls), 1)

    def test_lookup_butuh_sesi(self):
        if self.session.exists():
            self.session.unlink()
        app = create_app(
            store=self.store,
            scraper_factory=lambda: self.scraper,
            session_path=self.session,
            collector=self.collector,
            connect_inaproc_fn=lambda *args: _write_session(args[-1]),
            gateway_store=FakeGatewayStore(),
            gateway_client=FakeGatewayClient(),
        )
        client = TestClient(app)
        response = client.post("/api/lookup", json={"number": SAMPLE})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "belum_login")

    def test_lookup_nomor_invalid(self):
        response = self.client.post("/api/lookup", json={"number": "bad"})
        self.assertEqual(response.status_code, 422)

    def test_lookup_cache_empty_tanpa_scrape(self):
        self.store.checks[SAMPLE] = {"number": SAMPLE, "status": "empty"}
        response = self.client.post("/api/lookup", json={"number": SAMPLE})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["source"], "db")
        self.assertEqual(response.json()["status"], "empty")
        self.assertEqual(response.json()["items"], [])
        self.assertEqual(self.scraper.calls, [])

    def test_lookup_found_tanpa_baris_scrape_ulang(self):
        self.write_session()
        self.store.checks[SAMPLE] = {"number": SAMPLE, "status": "found"}
        response = self.client.post("/api/lookup", json={"number": SAMPLE})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["source"], "scrape")
        self.assertEqual(len(self.scraper.calls), 1)
        self.assertEqual(self.store.checks[SAMPLE]["status"], "found")

    def test_lookup_error_cache_scrape_ulang(self):
        self.write_session()
        self.store.checks[SAMPLE] = {
            "number": SAMPLE,
            "status": "error",
            "error_msg": "timeout",
        }
        response = self.client.post("/api/lookup", json={"number": SAMPLE})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["source"], "scrape")

    def test_lookup_upstream_timeout_jadi_504(self):
        from modules.inaproc.api.scraper import ScrapeError

        self.write_session()
        app = create_app(
            store=self.store,
            scraper_factory=lambda: FakeScraper(error=ScrapeError("request timeout")),
            session_path=self.session,
            collector=self.collector,
            connect_inaproc_fn=lambda email, password, path: _write_session(path),
            gateway_store=FakeGatewayStore(),
            gateway_client=FakeGatewayClient(),
        )
        client = TestClient(app)
        response = client.post("/api/lookup", json={"number": SAMPLE})
        self.assertEqual(response.status_code, 504)
        self.assertEqual(response.json()["error"], "upstream_timeout")

    def test_validasi_body_memakai_envelope_error_string(self):
        response = self.client.post("/api/lookup", json={})
        self.assertEqual(response.status_code, 422)
        body = response.json()
        self.assertIsInstance(body["error"], str)
        self.assertIn("message", body)

    def test_search_tidak_pernah_scrape(self):
        response = self.client.get("/api/search", params={"q": "acer"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.scraper.calls, [])

    def test_collect_job_aktif(self):
        self.collector.job = JobState(status="running")
        response = self.client.post(
            "/api/collect", json={"template": SAMPLE, "start": 1, "end": 2}
        )
        self.assertEqual(response.status_code, 409)

    def test_collect_validasi_rentang(self):
        response = self.client.post(
            "/api/collect", json={"template": SAMPLE, "start": 1, "end": 1002}
        )
        self.assertEqual(response.status_code, 422)

    def test_collect_preview(self):
        response = self.client.post(
            "/api/collect/preview", json={"template": SAMPLE, "start": 1, "end": 2500}
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total"], 2500)
        self.assertEqual(body["chunks"], 3)
        self.assertEqual(body["estimasi_menit"], 83.3)

    def test_collect_preview_delay_tidak_valid(self):
        response = self.client.post(
            "/api/collect/preview",
            json={"template": SAMPLE, "start": 1, "end": 10, "delay_min": 5, "delay_max": 2},
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"], "delay_tidak_valid")

    def test_collect_preview_menghitung_yang_sudah_ada(self):
        self.store.checks[str(SAMPLE.replace("11469", "1", 1))] = {
            "number": SAMPLE.replace("11469", "1", 1),
            "status": "found",
        }
        response = self.client.post(
            "/api/collect/preview", json={"template": SAMPLE, "start": 1, "end": 3}
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total"], 3)
        self.assertEqual(body["sudah_ada"], 1)
        self.assertEqual(body["akan_diproses"], 2)

    def test_collect_butuh_sesi(self):
        response = self.client.post(
            "/api/collect", json={"template": SAMPLE, "start": 1, "end": 2}
        )
        self.assertEqual(response.status_code, 401)

    def test_collect_meneruskan_delay_dan_force(self):
        self.write_session()
        captured = {}

        class FakeRunner:
            def __init__(self, store, scraper, *, delay_min, delay_max):
                captured["delay"] = (delay_min, delay_max)
                self.job = JobState(status="running")

            def collect(self, template, start, end, *, force=False):
                captured["force"] = force
                captured["range"] = (start, end)
                self.job = JobState(status="done", total=end - start + 1, empty=end - start + 1)

            def cancel(self):
                pass

        done = threading.Event()
        original_collect = FakeRunner.collect

        def collect_and_signal(self, *args, **kwargs):
            try:
                return original_collect(self, *args, **kwargs)
            finally:
                done.set()

        with patch("modules.inaproc.api.app.Collector", FakeRunner), patch.object(
            FakeRunner, "collect", collect_and_signal
        ):
            response = self.client.post(
                "/api/collect",
                json={
                    "template": SAMPLE,
                    "start": 10,
                    "end": 12,
                    "delay_min": 2,
                    "delay_max": 4,
                    "force": True,
                },
            )
            self.assertTrue(done.wait(timeout=2))
            for _ in range(50):
                if "force" in captured:
                    break
                time.sleep(0.01)

        self.assertEqual(response.status_code, 202)
        self.assertEqual(captured["delay"], (2.0, 4.0))
        self.assertEqual(captured["force"], True)
        self.assertEqual(captured["range"], (10, 12))

    def test_collect_cancel_tanpa_job(self):
        response = self.client.post("/api/collect/cancel")
        self.assertEqual(response.status_code, 409)

    def test_collect_menolak_lebih_dari_1000_nomor(self):
        response = self.client.post(
            "/api/collect", json={"template": SAMPLE, "start": 1, "end": 1001}
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"], "rentang_terlalu_besar")

    def test_collect_tepat_1000_nomor_diterima(self):
        self.write_session()
        response = self.client.post(
            "/api/collect",
            json={"template": SAMPLE, "start": 1, "end": 1000},
        )
        self.assertEqual(response.status_code, 202)
        body = response.json()
        self.assertEqual(body["total"], 1000)
        self.assertTrue(body["job_id"])
        self.assertEqual(body["job"]["total"], 1000)
        self.assertEqual(body["job"]["status"], "running")

    def test_collect_menghitung_sudah_ada_sebelum_thread_jalan(self):
        self.write_session()
        number = SAMPLE.replace("11469", "1", 1)
        self.store.checks[number] = {"number": number, "status": "empty"}
        release = threading.Event()

        class BlockingScraper:
            def fetch(self, _number):
                release.wait(timeout=5)
                return ScrapeResult(status="empty", rows=[])

        app = create_app(
            store=self.store,
            scraper_factory=lambda: BlockingScraper(),
            session_path=self.session,
            connect_inaproc_fn=lambda email, password, path: _write_session(path),
            gateway_store=FakeGatewayStore(),
            gateway_client=FakeGatewayClient(),
        )
        client = TestClient(app)
        try:
            response = client.post(
                "/api/collect",
                json={"template": SAMPLE, "start": 1, "end": 3},
            )
        finally:
            release.set()
        self.assertEqual(response.status_code, 202)
        body = response.json()
        self.assertEqual(body["total"], 3)
        self.assertEqual(body["sudah_ada"], 1)
        self.assertEqual(body["akan_diproses"], 2)
        self.assertEqual(body["job"]["total"], 3)

    def test_lookup_sesi_kedaluwarsa(self):
        self.write_session()
        app = create_app(
            store=self.store,
            scraper_factory=lambda: FakeScraper(error=AuthError("expired")),
            session_path=self.session,
            collector=self.collector,
            connect_inaproc_fn=lambda *args: _write_session(args[-1]),
            gateway_store=FakeGatewayStore(),
            gateway_client=FakeGatewayClient(),
        )
        client = TestClient(app)
        response = client.post("/api/lookup", json={"number": SAMPLE})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "belum_login")

    def test_status_idle(self):
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "idle")

    def test_export_csv(self):
        self.store.rows = [{"number": SAMPLE, "brand": "acer"}]
        response = self.client.get("/api/export", params={"format": "csv"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response.headers["content-type"])
        self.assertIn("brand", response.text)

    def test_export_json(self):
        self.store.rows = [{"number": SAMPLE, "brand": "acer"}]
        response = self.client.get("/api/export", params={"format": "json"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["brand"], "acer")

    def test_export_format_invalid(self):
        response = self.client.get("/api/export", params={"format": "xml"})
        self.assertEqual(response.status_code, 422)

    def test_export_menghormati_sort_dan_nama_file(self):
        self.store.rows = [{"number": SAMPLE, "brand": "acer"}]
        response = self.client.get(
            "/api/export",
            params={"format": "csv", "sort": "brand", "order": "desc"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("tkdn-", response.headers["content-disposition"])
        self.assertTrue(self.store.last_search["sort"] == "brand")
        self.assertTrue(self.store.last_search["order"] == "desc")

    def test_refresh_hapus_dan_ambil_ulang(self):
        self.write_session()
        self.store.checks[SAMPLE] = {"number": SAMPLE, "status": "found"}
        response = self.client.post("/api/refresh", json={"number": SAMPLE})
        self.assertEqual(response.status_code, 200)
        self.assertIn(SAMPLE, self.store.deleted)
        self.assertEqual(len(self.scraper.calls), 1)

    def test_refresh_nomor_belum_ada(self):
        response = self.client.post("/api/refresh", json={"number": SAMPLE})
        self.assertEqual(response.status_code, 404)

    def test_refresh_sesi_kedaluwarsa_tidak_menghapus_cache(self):
        self.write_session()
        self.store.checks[SAMPLE] = {"number": SAMPLE, "status": "found"}
        self.store.rows.append({"number": SAMPLE, "brand": "lama"})
        app = create_app(
            store=self.store,
            scraper_factory=lambda: FakeScraper(error=AuthError("expired")),
            session_path=self.session,
            collector=self.collector,
            connect_inaproc_fn=lambda *args: _write_session(args[-1]),
            gateway_store=FakeGatewayStore(),
            gateway_client=FakeGatewayClient(),
        )
        client = TestClient(app)
        response = client.post("/api/refresh", json={"number": SAMPLE})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "belum_login")
        self.assertIn(SAMPLE, self.store.checks)
        self.assertTrue(any(r["number"] == SAMPLE for r in self.store.rows))


if __name__ == "__main__":
    unittest.main()
