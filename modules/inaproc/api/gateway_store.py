from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Callable, Iterable, Sequence

GATEWAY_TABLES = (
    "inaproc_api_sync_runs",
    "inaproc_penyedia",
    "inaproc_produk",
    "inaproc_kategori",
    "inaproc_paket_epurchasing",
    "inaproc_transaksi_epurchasing",
    "inaproc_master_program",
)

_CREATE = (
    """
    CREATE TABLE IF NOT EXISTS inaproc_api_sync_runs (
        id          BIGINT AUTO_INCREMENT PRIMARY KEY,
        scope       VARCHAR(32) NOT NULL,
        params      JSON NULL,
        status      VARCHAR(16) NOT NULL,
        `cursor`    VARCHAR(255) NULL,
        pages       INT NOT NULL DEFAULT 0,
        total_items INT NOT NULL DEFAULT 0,
        error_code  VARCHAR(64) NULL,
        error_msg   TEXT NULL,
        started_at  DATETIME NOT NULL,
        last_ok_at  DATETIME NULL,
        finished_at DATETIME NULL,
        KEY idx_sync_scope_started (scope, started_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
      COMMENT='Audit setiap job sync INAPROC API Gateway; bukan data INAPROC'
    """,
    """
    CREATE TABLE IF NOT EXISTS inaproc_penyedia (
        kode_penyedia VARCHAR(64) PRIMARY KEY,
        nama_penyedia VARCHAR(255) NULL,
        npwp          VARCHAR(64) NULL,
        status        VARCHAR(64) NULL,
        source_url    VARCHAR(512) NULL,
        raw_json      JSON NULL,
        updated_at    DATETIME NOT NULL,
        source_updated_at DATETIME NULL,
        KEY idx_penyedia_nama (nama_penyedia)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
      COMMENT='Cache penyedia dari INAPROC API Gateway (read-only source)'
    """,
    """
    CREATE TABLE IF NOT EXISTS inaproc_produk (
        kd_produk     VARCHAR(64) PRIMARY KEY,
        kode_penyedia VARCHAR(64) NULL,
        kode_kategori VARCHAR(64) NULL,
        nama_produk   VARCHAR(512) NULL,
        kategori      VARCHAR(255) NULL,
        brand         VARCHAR(255) NULL,
        harga         DECIMAL(20,2) NULL,
        satuan        VARCHAR(64) NULL,
        source_url    VARCHAR(512) NULL,
        raw_json      JSON NULL,
        updated_at    DATETIME NOT NULL,
        source_updated_at DATETIME NULL,
        KEY idx_produk_nama (nama_produk),
        KEY idx_produk_brand (brand),
        KEY idx_produk_penyedia (kode_penyedia),
        KEY idx_produk_kategori (kode_kategori)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
      COMMENT='Cache produk e-katalog INAPROC; source_url untuk dibuka user'
    """,
    """
    CREATE TABLE IF NOT EXISTS inaproc_kategori (
        kode_kategori VARCHAR(64) PRIMARY KEY,
        nama_kategori VARCHAR(255) NULL,
        level         INT NULL,
        parent_kode   VARCHAR(64) NULL,
        source_url    VARCHAR(512) NULL,
        raw_json      JSON NULL,
        updated_at    DATETIME NOT NULL,
        source_updated_at DATETIME NULL,
        KEY idx_kategori_nama (nama_kategori),
        KEY idx_kategori_parent (parent_kode)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
      COMMENT='Cache master kategori e-katalog INAPROC per level'
    """,
    """
    CREATE TABLE IF NOT EXISTS inaproc_paket_epurchasing (
        kode_paket  VARCHAR(64) PRIMARY KEY,
        nama_paket  VARCHAR(512) NULL,
        tahun       INT NULL,
        kode_klpd   VARCHAR(64) NULL,
        total_nilai DECIMAL(20,2) NULL,
        source_url  VARCHAR(512) NULL,
        raw_json    JSON NULL,
        updated_at  DATETIME NOT NULL,
        source_updated_at DATETIME NULL,
        KEY idx_paket_tahun (tahun),
        KEY idx_paket_klpd (kode_klpd)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
      COMMENT='Cache paket e-purchasing INAPROC per KLPD dan tahun'
    """,
    """
    CREATE TABLE IF NOT EXISTS inaproc_transaksi_epurchasing (
        order_id      VARCHAR(64) PRIMARY KEY,
        kd_produk     VARCHAR(64) NULL,
        kode_penyedia VARCHAR(64) NULL,
        nama_produk   VARCHAR(512) NULL,
        jumlah        DECIMAL(20,2) NULL,
        total         DECIMAL(20,2) NULL,
        tahun         INT NULL,
        source_url    VARCHAR(512) NULL,
        raw_json      JSON NULL,
        updated_at    DATETIME NOT NULL,
        source_updated_at DATETIME NULL,
        KEY idx_transaksi_produk (kd_produk),
        KEY idx_transaksi_tahun (tahun)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
      COMMENT='Cache realisasi/transaksi e-purchasing per produk INAPROC'
    """,
    """
    CREATE TABLE IF NOT EXISTS inaproc_master_program (
        kode_program VARCHAR(64) PRIMARY KEY,
        nama_program VARCHAR(512) NULL,
        tahun        INT NULL,
        kode_klpd    VARCHAR(64) NULL,
        source_url   VARCHAR(512) NULL,
        raw_json     JSON NULL,
        updated_at   DATETIME NOT NULL,
        source_updated_at DATETIME NULL,
        KEY idx_program_nama (nama_program),
        KEY idx_program_tahun (tahun)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
      COMMENT='Cache master program INAPROC dari API Gateway'
    """,
)

# MySQL does not support "ADD COLUMN IF NOT EXISTS", so every column is
# checked against information_schema before running ALTER TABLE.
GATEWAY_COLUMN_MIGRATIONS: tuple[tuple[str, str, str], ...] = tuple(
    (table, "source_updated_at", "DATETIME NULL")
    for table in GATEWAY_TABLES
    if table != "inaproc_api_sync_runs"
) + (
    ("inaproc_api_sync_runs", "retry_status", "INT NULL"),
    ("inaproc_api_sync_runs", "retry_after", "DECIMAL(10,2) NULL"),
    ("inaproc_api_sync_runs", "retry_attempt", "INT NULL"),
)

_COMMENTS = {
    "inaproc_api_sync_runs": "Audit setiap job sync INAPROC API Gateway; bukan data INAPROC",
    "inaproc_penyedia": "Cache penyedia dari INAPROC API Gateway (read-only source)",
    "inaproc_produk": "Cache produk e-katalog INAPROC; source_url untuk dibuka user",
    "inaproc_kategori": "Cache master kategori e-katalog INAPROC per level",
    "inaproc_paket_epurchasing": "Cache paket e-purchasing INAPROC per KLPD dan tahun",
    "inaproc_transaksi_epurchasing": "Cache realisasi/transaksi e-purchasing per produk INAPROC",
    "inaproc_master_program": "Cache master program INAPROC dari API Gateway",
}

GATEWAY_SCHEMA_STATEMENTS = _CREATE + tuple(
    "ALTER TABLE " + table + " COMMENT='" + comment + "'"
    for table, comment in _COMMENTS.items()
)

class GatewayMysqlStore:
    def __init__(self, connection_factory: Callable[[], Any]) -> None:
        self._connect = connection_factory

    def create_schema(self) -> None:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                for statement in GATEWAY_SCHEMA_STATEMENTS:
                    cursor.execute(statement)
                self._ensure_columns(cursor)
            connection.commit()
        finally:
            connection.close()

    @staticmethod
    def _ensure_columns(cursor) -> None:
        """Add missing columns once; MySQL has no ADD COLUMN IF NOT EXISTS."""
        for table, column, definition in GATEWAY_COLUMN_MIGRATIONS:
            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA=DATABASE()
                  AND TABLE_NAME=%s
                  AND COLUMN_NAME=%s
                """,
                (table, column),
            )
            row = cursor.fetchone() or {}
            if int(row.get("total") or 0) > 0:
                continue
            cursor.execute(
                f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
            )

    def _run(self, operation):
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                result = operation(cursor)
            connection.commit()
            return result
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    # -- sync run audit -------------------------------------------------

    def start_run(self, scope: str, params: dict[str, Any] | None = None) -> int:
        def operation(cursor):
            cursor.execute(
                """
                INSERT INTO inaproc_api_sync_runs (scope, params, status, started_at)
                VALUES (%s, %s, 'running', %s)
                """,
                (scope, json.dumps(params or {}), datetime.utcnow()),
            )
            return int(cursor.lastrowid)

        return self._run(operation)

    def update_run(
        self,
        run_id: int,
        *,
        cursor: str | None = None,
        pages: int | None = None,
        total_items: int | None = None,
        status: str | None = None,
        retry_status: int | None = None,
        retry_after: float | None = None,
        retry_attempt: int | None = None,
    ) -> None:
        sets = ["last_ok_at=%s"]
        params: list[Any] = [datetime.utcnow()]
        if cursor is not None:
            sets.append("`cursor`=%s")
            params.append(cursor)
        if pages is not None:
            sets.append("pages=%s")
            params.append(pages)
        if total_items is not None:
            sets.append("total_items=%s")
            params.append(total_items)
        if status is not None:
            sets.append("status=%s")
            params.append(status)
        if retry_status is not None:
            sets.append("retry_status=%s")
            params.append(retry_status)
        if retry_after is not None:
            sets.append("retry_after=%s")
            params.append(retry_after)
        if retry_attempt is not None:
            sets.append("retry_attempt=%s")
            params.append(retry_attempt)
        params.append(run_id)
        self._run(
            lambda cur: cur.execute(
                f"UPDATE inaproc_api_sync_runs SET {', '.join(sets)} WHERE id=%s",
                tuple(params),
            )
        )

    def finish_run(
        self,
        run_id: int,
        status: str,
        *,
        error_code: str | None = None,
        error_msg: str | None = None,
    ) -> None:
        self._run(
            lambda cur: cur.execute(
                """
                UPDATE inaproc_api_sync_runs
                SET status=%s, error_code=%s, error_msg=%s, finished_at=%s
                WHERE id=%s
                """,
                (status, error_code, error_msg, datetime.utcnow(), run_id),
            )
        )

    def delete_run(self, run_id: int) -> None:
        self._run(
            lambda cur: cur.execute(
                "DELETE FROM inaproc_api_sync_runs WHERE id=%s",
                (run_id,),
            )
        )

    def last_run(self, scope: str | None = None) -> dict[str, Any] | None:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                if scope:
                    cursor.execute(
                        "SELECT * FROM inaproc_api_sync_runs WHERE scope=%s "
                        "ORDER BY id DESC LIMIT 1",
                        (scope,),
                    )
                else:
                    cursor.execute(
                        "SELECT * FROM inaproc_api_sync_runs ORDER BY id DESC LIMIT 1"
                    )
                return cursor.fetchone()
        finally:
            connection.close()

    # -- upserts --------------------------------------------------------

    def upsert_penyedia(self, rows: Sequence[dict[str, Any]], now: datetime) -> int:
        return self._upsert_many(
            "inaproc_penyedia",
            (
                "kode_penyedia",
                "nama_penyedia",
                "npwp",
                "status",
                "source_url",
                "raw_json",
                "updated_at",
                "source_updated_at",
            ),
            ("kode_penyedia",),
            rows,
            now,
        )

    def upsert_produk(self, rows: Sequence[dict[str, Any]], now: datetime) -> int:
        return self._upsert_many(
            "inaproc_produk",
            (
                "kd_produk",
                "kode_penyedia",
                "kode_kategori",
                "nama_produk",
                "kategori",
                "brand",
                "harga",
                "satuan",
                "source_url",
                "raw_json",
                "updated_at",
                "source_updated_at",
            ),
            ("kd_produk",),
            rows,
            now,
        )

    def delete_produk(self, kd_produk: str) -> None:
        self._run(
            lambda cur: cur.execute(
                "DELETE FROM inaproc_produk WHERE kd_produk=%s",
                (kd_produk,),
            )
        )

    def upsert_kategori(self, rows: Sequence[dict[str, Any]], now: datetime) -> int:
        return self._upsert_many(
            "inaproc_kategori",
            (
                "kode_kategori",
                "nama_kategori",
                "level",
                "parent_kode",
                "source_url",
                "raw_json",
                "updated_at",
                "source_updated_at",
            ),
            ("kode_kategori",),
            rows,
            now,
        )

    def upsert_paket(self, rows: Sequence[dict[str, Any]], now: datetime) -> int:
        return self._upsert_many(
            "inaproc_paket_epurchasing",
            (
                "kode_paket",
                "nama_paket",
                "tahun",
                "kode_klpd",
                "total_nilai",
                "source_url",
                "raw_json",
                "updated_at",
                "source_updated_at",
            ),
            ("kode_paket",),
            rows,
            now,
        )

    def upsert_transaksi(self, rows: Sequence[dict[str, Any]], now: datetime) -> int:
        return self._upsert_many(
            "inaproc_transaksi_epurchasing",
            (
                "order_id",
                "kd_produk",
                "kode_penyedia",
                "nama_produk",
                "jumlah",
                "total",
                "tahun",
                "source_url",
                "raw_json",
                "updated_at",
                "source_updated_at",
            ),
            ("order_id",),
            rows,
            now,
        )

    def upsert_program(self, rows: Sequence[dict[str, Any]], now: datetime) -> int:
        return self._upsert_many(
            "inaproc_master_program",
            (
                "kode_program",
                "nama_program",
                "tahun",
                "kode_klpd",
                "source_url",
                "raw_json",
                "updated_at",
                "source_updated_at",
            ),
            ("kode_program",),
            rows,
            now,
        )

    def _upsert_many(
        self,
        table: str,
        columns: tuple[str, ...],
        keys: tuple[str, ...],
        rows: Sequence[dict[str, Any]],
        now: datetime,
    ) -> int:
        if not rows:
            return 0
        placeholders = ", ".join(["%s"] * len(columns))
        updates = ", ".join(
            f"{col}=VALUES({col})" for col in columns if col not in keys
        )
        sql = (
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders}) "
            f"ON DUPLICATE KEY UPDATE {updates}"
        )

        def operation(cursor):
            for row in rows:
                values = []
                for column in columns:
                    if column == "updated_at":
                        values.append(now)
                    elif column == "source_updated_at":
                        values.append(row.get("source_updated_at") or _parse_datetime(row.get("updated_at")))
                    elif column == "raw_json":
                        values.append(json.dumps(row.get("raw_json") or row, ensure_ascii=False))
                    else:
                        values.append(row.get(column))
                cursor.execute(sql, tuple(values))
            return len(rows)

        return self._run(operation)

    # -- search ---------------------------------------------------------

    def search_produk(
        self,
        q: str = "",
        *,
        kode_penyedia: str | None = None,
        kategori: str | None = None,
        page: int = 1,
        per_page: int = 50,
        sort: str = "nama_produk",
        order: str = "asc",
    ) -> tuple[list[dict[str, Any]], int]:
        sort_columns = {
            "nama_produk": "nama_produk",
            "brand": "brand",
            "harga": "harga",
            "kategori": "kategori",
        }
        if sort not in sort_columns:
            raise ValueError(f"Unsupported sort column: {sort}")
        direction = "DESC" if str(order).lower() == "desc" else "ASC"
        clauses, params = _product_filters(q, kode_penyedia, kategori)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        limit = max(1, int(per_page))
        offset = max(0, (int(page) - 1) * limit)
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) AS total FROM inaproc_produk{where}", tuple(params))
                total = int((cursor.fetchone() or {}).get("total") or 0)
                cursor.execute(
                    "SELECT kd_produk, kode_penyedia, kode_kategori, nama_produk, "
                    "kategori, brand, harga, satuan, source_url, updated_at, source_updated_at "
                    f"FROM inaproc_produk{where} ORDER BY {sort_columns[sort]} {direction} "
                    "LIMIT %s OFFSET %s",
                    tuple(params + [limit, offset]),
                )
                return list(cursor.fetchall()), total
        finally:
            connection.close()

    def count_produk(self) -> int:
        return self._count("inaproc_produk")

    def count_paket(self) -> int:
        return self._count("inaproc_paket_epurchasing")

    def count_transaksi(self) -> int:
        return self._count("inaproc_transaksi_epurchasing")

    def search_paket(
        self,
        q: str = "",
        *,
        tahun: int | None = None,
        kode_klpd: str | None = None,
        page: int = 1,
        per_page: int = 50,
        sort: str = "nama_paket",
        order: str = "asc",
    ) -> tuple[list[dict[str, Any]], int]:
        sort_columns = {
            "nama_paket": "nama_paket",
            "tahun": "tahun",
            "total_nilai": "total_nilai",
            "kode_klpd": "kode_klpd",
        }
        if sort not in sort_columns:
            raise ValueError(f"Unsupported sort column: {sort}")
        direction = "DESC" if str(order).lower() == "desc" else "ASC"
        clauses, params = _paket_filters(q, tahun, kode_klpd)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        limit = max(1, int(per_page))
        offset = max(0, (int(page) - 1) * limit)
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT COUNT(*) AS total FROM inaproc_paket_epurchasing{where}",
                    tuple(params),
                )
                total = int((cursor.fetchone() or {}).get("total") or 0)
                cursor.execute(
                    "SELECT kode_paket, nama_paket, tahun, kode_klpd, total_nilai, "
                    "source_url, updated_at, source_updated_at "
                    f"FROM inaproc_paket_epurchasing{where} "
                    f"ORDER BY {sort_columns[sort]} {direction} "
                    "LIMIT %s OFFSET %s",
                    tuple(params + [limit, offset]),
                )
                return list(cursor.fetchall()), total
        finally:
            connection.close()

    def search_transaksi(
        self,
        q: str = "",
        *,
        tahun: int | None = None,
        kd_produk: str | None = None,
        kode_penyedia: str | None = None,
        page: int = 1,
        per_page: int = 50,
        sort: str = "tahun",
        order: str = "desc",
    ) -> tuple[list[dict[str, Any]], int]:
        sort_columns = {
            "nama_produk": "nama_produk",
            "jumlah": "jumlah",
            "total": "total",
            "tahun": "tahun",
        }
        if sort not in sort_columns:
            raise ValueError(f"Unsupported sort column: {sort}")
        direction = "DESC" if str(order).lower() == "desc" else "ASC"
        clauses, params = _transaksi_filters(q, tahun, kd_produk, kode_penyedia)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        limit = max(1, int(per_page))
        offset = max(0, (int(page) - 1) * limit)
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT COUNT(*) AS total FROM inaproc_transaksi_epurchasing{where}",
                    tuple(params),
                )
                total = int((cursor.fetchone() or {}).get("total") or 0)
                cursor.execute(
                    "SELECT order_id, kd_produk, kode_penyedia, nama_produk, jumlah, "
                    "total, tahun, source_url, updated_at, source_updated_at "
                    f"FROM inaproc_transaksi_epurchasing{where} "
                    f"ORDER BY {sort_columns[sort]} {direction} "
                    "LIMIT %s OFFSET %s",
                    tuple(params + [limit, offset]),
                )
                return list(cursor.fetchall()), total
        finally:
            connection.close()

    def _count(self, table: str) -> int:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) AS total FROM {table}")
                return int((cursor.fetchone() or {}).get("total") or 0)
        finally:
            connection.close()

def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None

def _product_filters(
    q: str,
    kode_penyedia: str | None,
    kategori: str | None,
) -> tuple[list[str], list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if q:
        like = f"%{q}%"
        clauses.append(
            "(LOWER(nama_produk) LIKE LOWER(%s) OR LOWER(brand) LIKE LOWER(%s) "
            "OR LOWER(kategori) LIKE LOWER(%s))"
        )
        params.extend([like] * 3)
    if kode_penyedia:
        clauses.append("kode_penyedia = %s")
        params.append(kode_penyedia)
    if kategori:
        clauses.append("LOWER(kategori) = LOWER(%s)")
        params.append(kategori)
    return clauses, params


def _paket_filters(
    q: str,
    tahun: int | None,
    kode_klpd: str | None,
) -> tuple[list[str], list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if q:
        like = f"%{q}%"
        clauses.append(
            "(LOWER(nama_paket) LIKE LOWER(%s) OR LOWER(kode_paket) LIKE LOWER(%s) "
            "OR LOWER(kode_klpd) LIKE LOWER(%s))"
        )
        params.extend([like] * 3)
    if tahun is not None:
        clauses.append("tahun = %s")
        params.append(int(tahun))
    if kode_klpd:
        clauses.append("kode_klpd = %s")
        params.append(kode_klpd)
    return clauses, params


def _transaksi_filters(
    q: str,
    tahun: int | None,
    kd_produk: str | None,
    kode_penyedia: str | None,
) -> tuple[list[str], list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if q:
        like = f"%{q}%"
        clauses.append(
            "(LOWER(nama_produk) LIKE LOWER(%s) OR LOWER(order_id) LIKE LOWER(%s) "
            "OR LOWER(kd_produk) LIKE LOWER(%s))"
        )
        params.extend([like] * 3)
    if tahun is not None:
        clauses.append("tahun = %s")
        params.append(int(tahun))
    if kd_produk:
        clauses.append("kd_produk = %s")
        params.append(kd_produk)
    if kode_penyedia:
        clauses.append("kode_penyedia = %s")
        params.append(kode_penyedia)
    return clauses, params
