from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from modules.inaproc.api.gateway import GatewayAuthError, GatewayDisabledError

logger = logging.getLogger(__name__)

SCOPES = {
    "penyedia": {
        "path": "/api/v1/ekatalog/penyedia-detail",
        "upsert": "upsert_penyedia",
        "mapper": "map_penyedia",
    },
    "produk": {
        "path": "/api/v1/ekatalog/list-produk-penyedia",
        "upsert": "upsert_produk",
        "mapper": "map_produk",
    },
    "kategori": {
        "path": "/api/v1/ekatalog/list-kategori-produk",
        "upsert": "upsert_kategori",
        "mapper": "map_kategori",
    },
    "paket": {
        "path": "/api/v1/ekatalog/paket-e-purchasing",
        "upsert": "upsert_paket",
        "mapper": "map_paket",
    },
    "transaksi": {
        "path": "/api/v1/ekatalog/e-purchasing-by-produk",
        "upsert": "upsert_transaksi",
        "mapper": "map_transaksi",
    },
    "program": {
        "path": "/api/v1/master/program",
        "upsert": "upsert_program",
        "mapper": "map_program",
    },
}

def _first(raw: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = raw.get(key)
        if value is not None:
            return value
    return None

def _base(raw: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "source_url": _first(raw, "url", "source_url", "link"),
        "raw_json": dict(raw),
    }

def map_penyedia(raw: Mapping[str, Any]) -> dict[str, Any]:
    return {
        **_base(raw),
        "kode_penyedia": str(_first(raw, "kode_penyedia", "kd_penyedia", "id") or ""),
        "nama_penyedia": _first(raw, "nama_penyedia", "nama", "name"),
        "npwp": _first(raw, "npwp"),
        "status": _first(raw, "status"),
    }

def map_produk(raw: Mapping[str, Any]) -> dict[str, Any]:
    return {
        **_base(raw),
        "kd_produk": str(_first(raw, "kd_produk", "kode_produk", "id") or ""),
        "kode_penyedia": _first(raw, "kode_penyedia", "kd_penyedia"),
        "kode_kategori": _first(raw, "kode_kategori", "kd_kategori"),
        "nama_produk": _first(raw, "nama_produk", "nama", "name"),
        "kategori": _first(raw, "kategori", "nama_kategori"),
        "brand": _first(raw, "brand", "merek"),
        "harga": _first(raw, "harga", "harga_satuan", "price"),
        "satuan": _first(raw, "satuan", "unit"),
    }

def map_kategori(raw: Mapping[str, Any]) -> dict[str, Any]:
    return {
        **_base(raw),
        "kode_kategori": str(_first(raw, "kode_kategori", "kd_kategori", "id") or ""),
        "nama_kategori": _first(raw, "nama_kategori", "nama", "name"),
        "level": _first(raw, "level", "tingkat"),
        "parent_kode": _first(raw, "parent_kode", "kode_parent"),
    }

def map_paket(raw: Mapping[str, Any]) -> dict[str, Any]:
    return {
        **_base(raw),
        "kode_paket": str(_first(raw, "kode_paket", "kd_paket", "id") or ""),
        "nama_paket": _first(raw, "nama_paket", "nama", "name"),
        "tahun": _first(raw, "tahun", "year"),
        "kode_klpd": _first(raw, "kode_klpd", "kd_klpd", "klpd"),
        "total_nilai": _first(raw, "total_nilai", "nilai"),
    }

def map_transaksi(raw: Mapping[str, Any]) -> dict[str, Any]:
    return {
        **_base(raw),
        "order_id": str(_first(raw, "order_id", "id") or ""),
        "kd_produk": _first(raw, "kd_produk", "kode_produk"),
        "kode_penyedia": _first(raw, "kode_penyedia", "kd_penyedia"),
        "nama_produk": _first(raw, "nama_produk", "nama", "name"),
        "jumlah": _first(raw, "jumlah", "qty", "quantity"),
        "total": _first(raw, "total", "total_harga"),
        "tahun": _first(raw, "tahun", "year"),
    }

def map_program(raw: Mapping[str, Any]) -> dict[str, Any]:
    return {
        **_base(raw),
        "kode_program": str(_first(raw, "kode_program", "kd_program", "id") or ""),
        "nama_program": _first(raw, "nama_program", "nama", "name"),
        "tahun": _first(raw, "tahun", "year"),
        "kode_klpd": _first(raw, "kode_klpd", "kd_klpd", "klpd"),
    }

MAPPERS = {
    "map_penyedia": map_penyedia,
    "map_produk": map_produk,
    "map_kategori": map_kategori,
    "map_paket": map_paket,
    "map_transaksi": map_transaksi,
    "map_program": map_program,
}

class GatewaySyncService:
    """Read Gateway data and upsert the normalized result into the app DB."""

    def __init__(
        self,
        store: Any,
        client: Any,
        *,
        clock: Callable[[], datetime] = datetime.utcnow,
    ) -> None:
        self.store = store
        self.client = client
        self._clock = clock

    def sync(
        self,
        scope: str,
        params: Mapping[str, Any] | None = None,
        *,
        force: bool = False,
        limit: int = 100,
        max_pages: int = 10_000,
    ) -> dict[str, Any]:
        config = SCOPES.get(scope)
        if config is None:
            raise ValueError(f"Unsupported gateway sync scope: {scope}")
        query = dict(params or {})
        if not force and scope == "produk" and self.store.count_produk() > 0:
            return {"scope": scope, "status": "skipped", "reason": "db_cache_exists"}
        if getattr(self.client, "enabled", True) is False:
            return {
                "scope": scope,
                "status": "failed",
                "error_code": "GATEWAY_DISABLED",
                "items": 0,
            }

        try:
            run_id = self.store.start_run(scope, query)
        except Exception as exc:
            logger.exception("Gateway sync could not start for scope=%s", scope)
            return {"scope": scope, "status": "failed", "error_code": "SYNC_FAILED", "items": 0}

        total = 0
        pages = 0
        cursor = None
        try:
            mapper = MAPPERS[config["mapper"]]
            upsert = getattr(self.store, config["upsert"])

            def record_cursor(value: str | None) -> None:
                nonlocal cursor
                cursor = value

            def record_retry(event: Mapping[str, Any]) -> None:
                # Mark the audit row as retrying before sleeping, then return it
                # to running so the final status reflects the actual outcome.
                self.store.update_run(
                    run_id,
                    cursor=cursor,
                    pages=pages,
                    total_items=total,
                    status="retrying",
                    retry_status=event.get("status_code"),
                    retry_after=event.get("retry_after"),
                    retry_attempt=event.get("attempt"),
                )
                self.store.update_run(
                    run_id,
                    cursor=cursor,
                    pages=pages,
                    total_items=total,
                    status="running",
                )

            if hasattr(self.client, "set_retry_callback"):
                self.client.set_retry_callback(record_retry)

            for page in self.client.paginate(
                config["path"],
                params=query,
                limit=limit,
                max_pages=max_pages,
                on_cursor=record_cursor,
            ):
                rows = [mapper(row) for row in page if isinstance(row, dict)]
                rows = [row for row in rows if _identity_ok(scope, row)]
                if rows:
                    upsert(rows, self._clock())
                total += len(rows)
                pages += 1
                self.store.update_run(
                    run_id,
                    cursor=cursor,
                    pages=pages,
                    total_items=total,
                    status="running",
                )
            self.store.finish_run(run_id, "success")
            return {"scope": scope, "status": "success", "items": total, "pages": pages}
        except (GatewayDisabledError, GatewayAuthError) as exc:
            code = "GATEWAY_DISABLED" if isinstance(exc, GatewayDisabledError) else "TOKEN_EXPIRED"
            self.store.finish_run(run_id, "failed", error_code=code, error_msg=str(exc))
            return {"scope": scope, "status": "failed", "error_code": code, "items": total}
        except Exception as exc:
            self.store.finish_run(
                run_id, "failed", error_code="SYNC_FAILED", error_msg=str(exc)
            )
            logger.exception("Gateway sync failed for scope=%s", scope)
            return {
                "scope": scope,
                "status": "failed",
                "error_code": "SYNC_FAILED",
                "items": total,
            }
        finally:
            if hasattr(self.client, "set_retry_callback"):
                self.client.set_retry_callback(None)

def _identity_ok(scope: str, row: Mapping[str, Any]) -> bool:
    keys = {
        "penyedia": "kode_penyedia",
        "produk": "kd_produk",
        "kategori": "kode_kategori",
        "paket": "kode_paket",
        "transaksi": "order_id",
        "program": "kode_program",
    }
    value = row.get(keys[scope])
    return bool(str(value).strip()) if value is not None else False
