import unittest
from datetime import datetime

from modules.inaproc.api.gateway import GatewayAuthError, GatewayDisabledError
from modules.inaproc.api.gateway_sync import GatewaySyncService, map_produk

class FakeStore:
    def __init__(self, total=0):
        self.total = total
        self.started = []
        self.updated = []
        self.finished = []
        self.upserts = []

    def count_produk(self):
        return self.total

    def start_run(self, scope, params=None):
        self.started.append((scope, params))
        return 1

    def update_run(self, run_id, **kwargs):
        self.updated.append((run_id, kwargs))

    def finish_run(self, run_id, status, **kwargs):
        self.finished.append((run_id, status, kwargs))

    def upsert_produk(self, rows, now):
        self.upserts.append(("produk", list(rows)))
        return len(rows)

    def upsert_penyedia(self, rows, now):
        self.upserts.append(("penyedia", list(rows)))
        return len(rows)

    def upsert_kategori(self, rows, now):
        self.upserts.append(("kategori", list(rows)))
        return len(rows)

    def upsert_paket(self, rows, now):
        self.upserts.append(("paket", list(rows)))
        return len(rows)

    def upsert_transaksi(self, rows, now):
        self.upserts.append(("transaksi", list(rows)))
        return len(rows)

    def upsert_program(self, rows, now):
        self.upserts.append(("program", list(rows)))
        return len(rows)

class FakeClient:
    def __init__(self, pages=None, error=None, enabled=True, retry_event=None):
        self.pages = pages or []
        self.error = error
        self.enabled = enabled
        self.calls = []
        self.retry_event = retry_event
        self.retry_callback = None

    def set_retry_callback(self, callback):
        self.retry_callback = callback

    def paginate(self, path, **kwargs):
        callback = kwargs.pop("on_cursor", None)
        self.calls.append((path, kwargs))
        if self.retry_callback is not None and self.retry_event is not None:
            self.retry_callback(self.retry_event)
        if self.error:
            raise self.error
        for index, page in enumerate(self.pages):
            if callback is not None:
                callback(f"cursor-{index}" if index + 1 < len(self.pages) else None)
            yield page

class GatewayMappingTest(unittest.TestCase):
    def test_map_produk_respons_resmi(self):
        raw = {
            "kd_produk": "K1",
            "nama_produk": "Monitor 24",
            "nama_penyedia": "PT Contoh",
            "kode_penyedia": "P1",
            "nama_kategori": "Monitor",
            "harga": "1500000",
            "satuan": "Unit",
            "url": "https://katalog.inaproc.id/produk/K1",
        }
        row = map_produk(raw)
        self.assertEqual(row["kd_produk"], "K1")
        self.assertEqual(row["kode_penyedia"], "P1")
        self.assertEqual(row["source_url"], "https://katalog.inaproc.id/produk/K1")
        self.assertEqual(row["raw_json"], raw)

    def test_map_produk_menerima_snake_case(self):
        row = map_produk(
            {
                "kd_produk": "K2",
                "kode_penyedia": "P2",
                "nama_produk": "Laptop",
                "kode_kategori": "C1",
                "harga": 9000000,
            }
        )
        self.assertEqual(row["nama_produk"], "Laptop")
        self.assertEqual(row["kode_kategori"], "C1")

class GatewaySyncTest(unittest.TestCase):
    def test_sync_produk_memanggil_api_dan_upsert(self):
        store = FakeStore()
        client = FakeClient(
            pages=[[{"kd_produk": "K1", "nama_produk": "Monitor", "kode_penyedia": "P1"}]]
        )
        service = GatewaySyncService(store, client)
        result = service.sync("produk", {"kode_penyedia": "P1"})
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["items"], 1)
        self.assertEqual(client.calls[0][0], "/api/v1/ekatalog/list-produk-penyedia")
        self.assertEqual(store.upserts[0][0], "produk")
        self.assertEqual(store.finished[0][1], "success")

    def test_sync_scope_tidak_dikenal(self):
        service = GatewaySyncService(FakeStore(), FakeClient())
        with self.assertRaises(ValueError):
            service.sync("drop-table")

    def test_db_first_skip_bila_data_sudah_ada(self):
        store = FakeStore(total=10)
        client = FakeClient()
        service = GatewaySyncService(store, client)
        result = service.sync("produk", {"kode_penyedia": "P1"}, force=False)
        self.assertEqual(result["status"], "skipped")
        self.assertEqual(client.calls, [])
        self.assertEqual(store.started, [])

    def test_force_tetap_sync(self):
        store = FakeStore(total=10)
        client = FakeClient(pages=[[{"kd_produk": "K1"}]])
        result = GatewaySyncService(store, client).sync("produk", {}, force=True)
        self.assertEqual(result["status"], "success")

    def test_token_expired_tidak_retry_dan_audit_failed(self):
        store = FakeStore()
        client = FakeClient(error=GatewayAuthError("expired"))
        result = GatewaySyncService(store, client).sync("produk", {}, force=True)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error_code"], "TOKEN_EXPIRED")
        self.assertEqual(store.finished[0][1], "failed")

    def test_disabled_tidak_memanggil_api(self):
        store = FakeStore()
        client = FakeClient(error=GatewayDisabledError("disabled"), enabled=False)
        result = GatewaySyncService(store, client).sync("produk", {}, force=True)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error_code"], "GATEWAY_DISABLED")
        self.assertEqual(store.started, [])

    def test_progress_update_per_halaman(self):
        store = FakeStore()
        client = FakeClient(pages=[[{"kd_produk": "K1"}], [{"kd_produk": "K2"}]])
        GatewaySyncService(store, client).sync("produk", {}, force=True)
        self.assertTrue(any(entry[1].get("total_items") == 2 for entry in store.updated))

    def test_retry_429_tercatat_di_audit(self):
        store = FakeStore()
        client = FakeClient(
            pages=[[{"kd_produk": "K1"}]],
            retry_event={"status_code": 429, "retry_after": 1.5, "attempt": 1},
        )
        result = GatewaySyncService(store, client).sync("produk", {}, force=True)
        self.assertEqual(result["status"], "success")
        self.assertTrue(
            any(
                kwargs.get("status") == "retrying"
                and kwargs.get("retry_status") == 429
                and kwargs.get("retry_after") == 1.5
                for _, kwargs in store.updated
            )
        )

if __name__ == "__main__":
    unittest.main()
