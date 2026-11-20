from __future__ import annotations

import re
import threading
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from modules.inaproc.api.auth import AuthError, connect_inaproc, muat_storage_state
from modules.inaproc.api.cache import TkdnMysqlStore
from modules.inaproc.api.collector import Collector, JobState, utc_now_naive
from modules.inaproc.api.config import InaprocConfigError, InaprocDbConfig, load_env_file
from modules.inaproc.api.db import DbUnavailableError, connect_mysql
from modules.inaproc.api.exporter import (
    PAKET_COLUMNS,
    PRODUK_COLUMNS,
    TRANSAKSI_COLUMNS,
    to_csv,
    to_json,
)
from modules.inaproc.api.gateway import GatewayConfig, InaprocGatewayClient
from modules.inaproc.api.gateway_jobs import GatewayJobError, GatewayJobManager
from modules.inaproc.api.gateway_store import GatewayMysqlStore
from modules.inaproc.api.gateway_sync import GatewaySyncService, SCOPES
from modules.inaproc.api.scraper import ScrapeError, TkdnScraper
from modules.inaproc.api.schemas import (
    CollectRequest,
    LoginRequest,
    LookupRequest,
    PreviewRequest,
    RefreshRequest,
    SearchParams,
    validate_delay,
)
from modules.inaproc.api.spt import SptNumber, sequence_range

DEFAULT_SESSION_PATH = Path("modules/inaproc/storageState.json")
ERROR_CODE_RE = re.compile(r"(?:^|\b)([a-z_]+):")


def _error(code: str, message: str, status: int) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message})


def _error_code_from(message: str, fallback: str) -> str:
    match = ERROR_CODE_RE.search(message or "")
    return match.group(1) if match else fallback


def _lookup_from_db(store, number: str) -> list[dict[str, Any]]:
    return store.search(number=number, per_page=1000)

def _save_result(store, number: str, result) -> None:
    now = _utc_now_naive()
    if result.status == "found":
        save = getattr(store, "save_found", None)
        if callable(save):
            save(number, result.rows, now)
        else:
            store.upsert_rows(number, result.rows, now)
            store.upsert_check(number, "found", None, now)
    else:
        save = getattr(store, "save_empty", None)
        if callable(save):
            save(number, now)
        else:
            store.delete_rows_for_number(number)
            store.upsert_check(number, "empty", None, now)


def _utc_now_naive() -> datetime:
    return utc_now_naive()


def _local_iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def create_app(
    *,
    store=None,
    scraper_factory: Callable[[], Any] | None = None,
    session_path: str | Path = DEFAULT_SESSION_PATH,
    collector=None,
    connect_inaproc_fn=connect_inaproc,
    gateway_store=None,
    gateway_client=None,
    gateway_sync_service=None,
    web_dist: str | Path | None = None,
) -> FastAPI:
    load_env_file()
    session = Path(session_path)
    db_config = None
    if store is None:
        db_config = InaprocDbConfig.from_env()
        store = TkdnMysqlStore(lambda: connect_mysql(db_config))
    if gateway_store is None:
        if db_config is None:
            db_config = InaprocDbConfig.from_env()
        gateway_store = GatewayMysqlStore(lambda: connect_mysql(db_config))
    if gateway_client is None:
        gateway_client = InaprocGatewayClient(GatewayConfig.from_env())
    if gateway_sync_service is None:
        gateway_sync_service = GatewaySyncService(gateway_store, gateway_client)
    gateway_jobs = GatewayJobManager(gateway_sync_service)
    if scraper_factory is None:
        scraper_factory = lambda: TkdnScraper(session)
    if collector is None:
        collector = Collector(store, scraper_factory())
    job_holder = {"collector": collector}
    job_lock = threading.Lock()
    dist = Path(web_dist) if web_dist else Path(__file__).resolve().parent.parent / "web" / "dist"

    @asynccontextmanager
    async def lifespan(_app):
        store.create_schema()
        gateway_store.create_schema()
        yield

    app = FastAPI(title="INAPROC TKDN Search", version="1.0.0", lifespan=lifespan)
    app.state.store = store
    app.state.gateway_store = gateway_store
    app.state.gateway_jobs = gateway_jobs
    app.state.session_path = session
    app.state.job_holder = job_holder
    app.state.web_dist = dist

    @app.exception_handler(DbUnavailableError)
    async def _db_error(request, exc):
        return JSONResponse(
            status_code=503,
            content={"error": "db_unavailable", "message": str(exc)},
        )

    @app.exception_handler(HTTPException)
    async def _http_error(request, exc):
        detail = exc.detail
        if isinstance(detail, dict) and "code" in detail:
            return JSONResponse(
                status_code=exc.status_code,
                content={"error": detail["code"], "message": detail.get("message", "")},
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "http_error", "message": str(detail)},
        )

    @app.exception_handler(RequestValidationError)
    async def _request_validation_error(request, exc):
        errors = exc.errors()
        raw = errors[0].get("msg", "") if errors else ""
        message = str(raw)
        if message.startswith("Value error, "):
            message = message[len("Value error, "):]
        return JSONResponse(
            status_code=422,
            content={"error": _error_code_from(message, "request_tidak_valid"), "message": message},
        )

    @app.exception_handler(ValidationError)
    async def _validation_error(request, exc):
        message = str(exc)
        return JSONResponse(
            status_code=422,
            content={"error": _error_code_from(message, "request_tidak_valid"), "message": message},
        )

    @app.exception_handler(Exception)
    async def _unhandled_error(request, exc):
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "message": "Internal server error"},
        )

    @app.get("/api/session")
    def session_status():
        if not session.exists():
            return {"configured": False, "valid": None, "checked_at": _local_iso_now()}
        try:
            muat_storage_state(session)
        except AuthError:
            return {"configured": False, "valid": False, "checked_at": _local_iso_now()}
        return {"configured": True, "valid": True, "checked_at": _local_iso_now()}

    @app.post("/api/login")
    def login(payload: LoginRequest):
        try:
            result = connect_inaproc_fn(payload.email, payload.password, session)
        except AuthError as exc:
            message = str(exc)
            code = "butuh_interaksi" if "otp" in message.lower() or "captcha" in message.lower() else "kredensial_salah"
            raise _error(code, message, 409 if code == "butuh_interaksi" else 401)
        configured = session.exists()
        return {
            "ok": configured,
            "session": {"configured": configured, "valid": configured},
            "connected": configured,
            "configured": configured,
            "session_path": result.get("session_path"),
        }

    @app.post("/api/logout")
    def logout():
        if session.exists():
            session.unlink()
        return {"ok": True, "session": {"configured": False, "valid": None}}

    @app.get("/api/search")
    def search(
        q: str = "",
        brand: str | None = None,
        min_value: float | None = None,
        page: int = Query(1, ge=1),
        per_page: int = Query(50, ge=1, le=200),
        sort: str = "number",
        order: str = "asc",
    ):
        try:
            params = SearchParams(
                q=q,
                brand=brand,
                min_value=min_value,
                page=page,
                per_page=per_page,
                sort=sort,
                order=order,
            )
        except ValidationError as exc:
            raise _error("filter_tidak_valid", str(exc), 422)
        rows = store.search(
            q=params.q,
            brand=params.brand,
            min_value=params.min_value,
            page=params.page,
            per_page=params.per_page,
            sort=params.sort,
            order=params.order,
        )
        total = store.count(
            q=params.q,
            brand=params.brand,
            min_value=params.min_value,
        )
        return {
            "items": rows,
            "page": params.page,
            "per_page": params.per_page,
            "total": total,
        }

    def _needs_scrape(number: str, *, force: bool = False) -> bool:
        if force:
            return True
        check = store.get_check(number)
        if not check:
            return True
        status = check.get("status")
        if status == "found":
            return not _lookup_from_db(store, number)
        if status == "empty":
            rows = _lookup_from_db(store, number)
            if rows:
                store.delete_rows_for_number(number)
            return False
        return True

    @app.post("/api/lookup")
    def lookup(payload: LookupRequest):
        number = payload.number
        if not _needs_scrape(number, force=payload.force):
            rows = _lookup_from_db(store, number)
            check = store.get_check(number) or {}
            return {"source": "db", "status": check.get("status", "found"), "items": rows}
        check = store.get_check(number)
        if check and check.get("status") == "found" and not _lookup_from_db(store, number):
            store.upsert_check(number, "error", "data_tidak_konsisten", _utc_now_naive())
        if not session.exists():
            raise _error("belum_login", "Connect the INAPROC provider session first", 401)
        scraper = scraper_factory()
        try:
            result = scraper.fetch(SptNumber.parse(number))
        except AuthError as exc:
            raise _error("belum_login", str(exc), 401)
        except ScrapeError as exc:
            store.upsert_check(number, "error", str(exc), _utc_now_naive())
            code = "upstream_timeout" if "timeout" in str(exc).lower() else "upstream_error"
            raise _error(code, str(exc), 504 if code == "upstream_timeout" else 502)
        _save_result(store, number, result)
        return {"source": "scrape", "status": result.status, "items": result.rows}

    def _preview(payload: PreviewRequest, delay_min: float, delay_max: float) -> dict[str, Any]:
        numbers = [str(n) for n in sequence_range(SptNumber.parse(payload.template), payload.start, payload.end)]
        existing = {c["number"] for c in store.get_checks(numbers) if c.get("status") in {"found", "empty"}}
        total = len(numbers)
        akan_diproses = total - len(existing)
        return {
            "total": total,
            "sudah_ada": len(existing),
            "akan_diproses": akan_diproses,
            "estimasi_menit": round((akan_diproses * ((delay_min + delay_max) / 2)) / 60, 1),
            "chunks": max(1, (total + 999) // 1000),
        }

    @app.post("/api/collect/preview")
    def collect_preview(payload: PreviewRequest):
        try:
            validate_delay(payload.delay_min, payload.delay_max)
        except ValueError as exc:
            raise _error("delay_tidak_valid", str(exc), 422)
        return _preview(payload, payload.delay_min, payload.delay_max)

    @app.post("/api/collect", status_code=202)
    def collect(payload: CollectRequest):
        active = job_holder["collector"]
        with job_lock:
            if active.job.status in {"running", "cancelling"}:
                raise _error("job_aktif", "A collect job is already running", 409)
            if not session.exists():
                raise _error("belum_login", "Connect the INAPROC provider session first", 401)
            runner = Collector(
                store,
                scraper_factory(),
                delay_min=payload.delay_min,
                delay_max=payload.delay_max,
            )
            job_holder["collector"] = runner
            template = SptNumber.parse(payload.template)
            # Prepare the job before starting the worker so the 202 response
            # always carries a real job_id, total, and cache count.
            prepare = getattr(runner, "prepare", None)
            if callable(prepare):
                prepare(template, payload.start, payload.end)
            numbers = [
                str(n) for n in sequence_range(template, payload.start, payload.end)
            ]
            sudah_ada = 0
            if not payload.force:
                checks = store.get_checks(numbers)
                sudah_ada = sum(
                    1
                    for check in checks
                    if check.get("status") in {"found", "empty"}
                    and (
                        check.get("status") == "empty"
                        or int(check.get("row_count") or 1) > 0
                    )
                )

            def _run():
                runner.collect(
                    template,
                    payload.start,
                    payload.end,
                    force=payload.force,
                )

            threading.Thread(target=_run, daemon=True).start()
        return {
            "job_id": runner.job.job_id,
            "status": runner.job.status,
            "nomor": runner.job.template,
            "total": runner.job.total,
            "sudah_ada": sudah_ada,
            "akan_diproses": runner.job.total - sudah_ada,
            "accepted": True,
            "job": runner.job.as_dict(),
        }

    @app.post("/api/collect/cancel")
    def collect_cancel():
        active = job_holder["collector"]
        if active.job.status not in {"running", "cancelling"}:
            raise _error("tidak_ada_job", "No collect job is running", 409)
        active.cancel()
        return {"status": "cancelling", "cancelling": True}

    @app.get("/api/status")
    def status():
        job = job_holder["collector"].job
        if job.status == "idle":
            return {"status": "idle"}
        return job.as_dict()

    @app.get("/api/export")
    def export(
        format: str = "csv",
        q: str = "",
        brand: str | None = None,
        min_value: float | None = None,
        sort: str = "number",
        order: str = "asc",
    ):
        if format not in {"csv", "json"}:
            raise _error("format_tidak_valid", "format must be csv or json", 422)
        try:
            rows = store.search(
                q=q,
                brand=brand,
                min_value=min_value,
                page=1,
                per_page=100_000,
                sort=sort,
                order=order,
            )
        except ValueError as exc:
            raise _error("filter_tidak_valid", str(exc), 422)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        if format == "csv":
            return Response(
                content=to_csv(rows),
                media_type="text/csv; charset=utf-8",
                headers={
                    "Content-Disposition": f'attachment; filename="tkdn-{stamp}.csv"'
                },
            )
        return Response(
            content=to_json(rows),
            media_type="application/json; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="tkdn-{stamp}.json"'
            },
        )

    @app.post("/api/refresh")
    def refresh(payload: RefreshRequest):
        number = payload.number
        if store.get_check(number) is None:
            raise _error("nomor_tidak_ditemukan", "Number is not in the cache", 404)
        if job_holder["collector"].job.status in {"running", "cancelling"}:
            raise _error("job_aktif", "A collect job is already running", 409)
        if not session.exists():
            raise _error("belum_login", "Connect the INAPROC provider session first", 401)
        try:
            result = scraper_factory().fetch(SptNumber.parse(number))
        except AuthError as exc:
            raise _error("belum_login", str(exc), 401)
        except ScrapeError as exc:
            store.upsert_check(number, "error", str(exc), _utc_now_naive())
            code = "upstream_timeout" if "timeout" in str(exc).lower() else "upstream_error"
            raise _error(code, str(exc), 504 if code == "upstream_timeout" else 502)
        store.delete_number(number)
        _save_result(store, number, result)
        return {"source": "scrape", "status": result.status, "items": result.rows}

    @app.get("/api/gateway/status")
    def gateway_status():
        try:
            produk_count = gateway_store.count_produk()
            paket_count = gateway_store.count_paket()
            transaksi_count = gateway_store.count_transaksi()
            last_run = gateway_store.last_run()
        except DbUnavailableError:
            raise
        except Exception:
            produk_count = paket_count = transaksi_count = 0
            last_run = None
        return {
            "enabled": bool(getattr(gateway_client, "enabled", False)),
            "scopes": list(SCOPES),
            "produk_count": produk_count,
            "paket_count": paket_count,
            "transaksi_count": transaksi_count,
            "last_run": last_run,
        }

    @app.get("/api/gateway/produk")
    def gateway_produk(
        q: str = "",
        kode_penyedia: str | None = None,
        kategori: str | None = None,
        page: int = Query(1, ge=1),
        per_page: int = Query(50, ge=1, le=200),
        sort: str = "nama_produk",
        order: str = "asc",
    ):
        try:
            rows, total = gateway_store.search_produk(
                q=q,
                kode_penyedia=kode_penyedia,
                kategori=kategori,
                page=page,
                per_page=per_page,
                sort=sort,
                order=order,
            )
        except ValueError as exc:
            raise _error("filter_tidak_valid", str(exc), 422)
        return {
            "items": rows,
            "page": page,
            "per_page": per_page,
            "total": total,
        }

    @app.get("/api/gateway/epurchasing")
    def gateway_epurchasing(
        kind: str = "paket",
        q: str = "",
        tahun: int | None = None,
        kode_klpd: str | None = None,
        kd_produk: str | None = None,
        kode_penyedia: str | None = None,
        page: int = Query(1, ge=1),
        per_page: int = Query(50, ge=1, le=200),
        sort: str | None = None,
        order: str = "desc",
    ):
        if kind not in {"paket", "transaksi"}:
            raise _error("kind_tidak_valid", "kind must be paket or transaksi", 422)
        try:
            if kind == "paket":
                rows, total = gateway_store.search_paket(
                    q=q,
                    tahun=tahun,
                    kode_klpd=kode_klpd,
                    page=page,
                    per_page=per_page,
                    sort=sort or "nama_paket",
                    order=order,
                )
            else:
                rows, total = gateway_store.search_transaksi(
                    q=q,
                    tahun=tahun,
                    kd_produk=kd_produk,
                    kode_penyedia=kode_penyedia,
                    page=page,
                    per_page=per_page,
                    sort=sort or "tahun",
                    order=order,
                )
        except ValueError as exc:
            raise _error("filter_tidak_valid", str(exc), 422)
        return {
            "kind": kind,
            "items": rows,
            "page": page,
            "per_page": per_page,
            "total": total,
        }

    @app.get("/api/gateway/export")
    def gateway_export(
        kind: str = "produk",
        format: str = "csv",
        q: str = "",
        kode_penyedia: str | None = None,
        kategori: str | None = None,
        tahun: int | None = None,
        kode_klpd: str | None = None,
        kd_produk: str | None = None,
    ):
        if kind not in {"produk", "paket", "transaksi"}:
            raise _error("kind_tidak_valid", "kind must be produk, paket, or transaksi", 422)
        if format not in {"csv", "json"}:
            raise _error("format_tidak_valid", "format must be csv or json", 422)
        try:
            if kind == "produk":
                rows, _ = gateway_store.search_produk(
                    q=q,
                    kode_penyedia=kode_penyedia,
                    kategori=kategori,
                    page=1,
                    per_page=100_000,
                )
                columns = PRODUK_COLUMNS
            elif kind == "paket":
                rows, _ = gateway_store.search_paket(
                    q=q,
                    tahun=tahun,
                    kode_klpd=kode_klpd,
                    page=1,
                    per_page=100_000,
                )
                columns = PAKET_COLUMNS
            else:
                rows, _ = gateway_store.search_transaksi(
                    q=q,
                    tahun=tahun,
                    kd_produk=kd_produk,
                    kode_penyedia=kode_penyedia,
                    page=1,
                    per_page=100_000,
                )
                columns = TRANSAKSI_COLUMNS
        except ValueError as exc:
            raise _error("filter_tidak_valid", str(exc), 422)
        content = to_csv(rows, columns) if format == "csv" else to_json(rows, columns)
        media_type = "text/csv; charset=utf-8" if format == "csv" else "application/json; charset=utf-8"
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="inaproc-{kind}.{format}"'},
        )

    @app.post("/api/gateway/sync/{scope}", status_code=202)
    def gateway_sync_scope(scope: str, payload: dict[str, Any] | None = None):
        body = payload or {}
        if getattr(gateway_client, "enabled", False) is False:
            raise _error(
                "gateway_disabled",
                "INAPROC API Gateway is disabled; configure INAPROC_API_TOKEN first",
                503,
            )
        try:
            state = gateway_jobs.start(
                scope,
                body.get("params") or {},
                force=bool(body.get("force", False)),
            )
        except GatewayJobError as exc:
            raise _error(exc.code, str(exc), 409 if exc.code == "job_aktif" else 422)
        return {"job": state}

    @app.get("/api/gateway/sync/{scope}/status")
    def gateway_sync_status(scope: str):
        try:
            return gateway_jobs.status(scope)
        except GatewayJobError as exc:
            raise _error(exc.code, str(exc), 422)

    if dist.is_dir():
        assets = dist / "assets"
        if assets.is_dir():
            app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        def spa(full_path: str, request: Request):
            if full_path.startswith("api/"):
                return JSONResponse(status_code=404, content={"error": "not_found", "message": "Not found"})
            candidate = (dist / full_path).resolve()
            try:
                candidate.relative_to(dist.resolve())
            except ValueError:
                return JSONResponse(status_code=404, content={"error": "not_found", "message": "Not found"})
            if full_path and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(dist / "index.html")

    return app
