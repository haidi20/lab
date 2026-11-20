from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Callable, Iterable, Sequence

SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS tkdn_rows (
        id               BIGINT AUTO_INCREMENT PRIMARY KEY,
        number           VARCHAR(128) NOT NULL,
        specification_id VARCHAR(128) NULL,
        product_type     VARCHAR(255) NULL,
        brand            VARCHAR(255) NULL,
        type             VARCHAR(255) NULL,
        description      VARCHAR(512) NULL,
        standard         VARCHAR(255) NULL,
        value            DOUBLE NULL,
        hs               VARCHAR(64) NULL,
        fetched_at       DATETIME NOT NULL,
        row_hash         CHAR(64) NOT NULL,
        UNIQUE KEY uq_tkdn_row (row_hash),
        KEY idx_tkdn_brand (brand),
        KEY idx_tkdn_number (number)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
      COMMENT='Baris hasil scraping TKDN per nomor SPT; cache utama pencarian'
    """,
    """
    CREATE TABLE IF NOT EXISTS tkdn_checks (
        number     VARCHAR(128) PRIMARY KEY,
        status     VARCHAR(16) NOT NULL,
        checked_at DATETIME NOT NULL,
        error_msg  TEXT NULL,
        KEY idx_tkdn_checks_status (status)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
      COMMENT='Status pengecekan per nomor SPT (found/empty/error) untuk skip collect'
    """,
)

# CREATE TABLE IF NOT EXISTS does not update comments on an existing table.
COMMENT_STATEMENTS = (
    "ALTER TABLE tkdn_rows COMMENT='Baris hasil scraping TKDN per nomor SPT; cache utama pencarian'",
    "ALTER TABLE tkdn_checks COMMENT='Status pengecekan per nomor SPT (found/empty/error) untuk skip collect'",
)


class TkdnMysqlStore:
    def __init__(self, connection_factory: Callable[[], Any]) -> None:
        self._connect = connection_factory

    def create_schema(self) -> None:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                for statement in SCHEMA_STATEMENTS:
                    cursor.execute(statement)
                for statement in COMMENT_STATEMENTS:
                    cursor.execute(statement)
            connection.commit()
        finally:
            connection.close()

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

    def save_found(self, number: str, rows: Sequence[dict[str, Any]], fetched_at: datetime) -> None:
        """Replace one number's rows and mark it found in a single transaction."""
        self._replace_rows(number, rows, "found", None, fetched_at)

    def save_empty(self, number: str, checked_at: datetime) -> None:
        """Delete stale rows and mark one number empty in a single transaction."""
        self._replace_rows(number, [], "empty", None, checked_at)

    def _replace_rows(
        self,
        number: str,
        rows: Sequence[dict[str, Any]],
        status: str,
        error_msg: str | None,
        checked_at: datetime,
    ) -> None:
        def operation(cursor):
            cursor.execute("DELETE FROM tkdn_rows WHERE number=%s", (number,))
            for row in rows:
                cursor.execute(
                    """
                    INSERT INTO tkdn_rows (
                        number, specification_id, product_type, brand, type,
                        description, standard, value, hs, fetched_at, row_hash
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        product_type=VALUES(product_type),
                        brand=VALUES(brand),
                        type=VALUES(type),
                        description=VALUES(description),
                        standard=VALUES(standard),
                        value=VALUES(value),
                        hs=VALUES(hs),
                        fetched_at=VALUES(fetched_at)
                    """,
                    (
                        number,
                        row.get("specification_id"),
                        row.get("product_type"),
                        row.get("brand"),
                        row.get("type"),
                        row.get("description"),
                        row.get("standard"),
                        row.get("value"),
                        row.get("hs"),
                        checked_at,
                        row_hash(number, row),
                    ),
                )
            cursor.execute(
                """
                INSERT INTO tkdn_checks (number, status, checked_at, error_msg)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    status=VALUES(status),
                    checked_at=VALUES(checked_at),
                    error_msg=VALUES(error_msg)
                """,
                (number, status, checked_at, error_msg),
            )

        self._run(operation)

    def should_skip(self, number: str) -> bool:
        """Return true only for consistent final cache entries.

        A found row without tkdn_rows is reset to error so collect can retry it.
        An empty row with orphan tkdn_rows is cleaned without scraping again.
        """
        check = self.get_check(number)
        if not check:
            return False
        status = check.get("status")
        row_count = int(check.get("row_count") or 0)
        if status == "found" and row_count == 0:
            self.upsert_check(number, "error", "data_tidak_konsisten", datetime.utcnow())
            return False
        if status == "empty" and row_count > 0:
            self.delete_rows_for_number(number)
            return True
        return status in {"found", "empty"} and (status == "empty" or row_count > 0)

    def upsert_rows(self, number: str, rows: Sequence[dict[str, Any]], fetched_at: datetime) -> None:
        if not rows:
            return

        def operation(cursor):
            for row in rows:
                cursor.execute(
                    """
                    INSERT INTO tkdn_rows (
                        number, specification_id, product_type, brand, type,
                        description, standard, value, hs, fetched_at, row_hash
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        product_type=VALUES(product_type),
                        brand=VALUES(brand),
                        type=VALUES(type),
                        description=VALUES(description),
                        standard=VALUES(standard),
                        value=VALUES(value),
                        hs=VALUES(hs),
                        fetched_at=VALUES(fetched_at)
                    """,
                    (
                        number,
                        row.get("specification_id"),
                        row.get("product_type"),
                        row.get("brand"),
                        row.get("type"),
                        row.get("description"),
                        row.get("standard"),
                        row.get("value"),
                        row.get("hs"),
                        fetched_at,
                        row_hash(number, row),
                    ),
                )

        self._run(operation)

    def delete_rows_for_number(self, number: str) -> None:
        self._run(lambda cursor: cursor.execute("DELETE FROM tkdn_rows WHERE number=%s", (number,)))

    def upsert_check(
        self,
        number: str,
        status: str,
        error_msg: str | None,
        checked_at: datetime,
    ) -> None:
        self._run(
            lambda cursor: cursor.execute(
                """
                INSERT INTO tkdn_checks (number, status, checked_at, error_msg)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    status=VALUES(status),
                    checked_at=VALUES(checked_at),
                    error_msg=VALUES(error_msg)
                """,
                (number, status, checked_at, error_msg),
            )
        )

    def delete_number(self, number: str) -> None:
        def operation(cursor):
            cursor.execute("DELETE FROM tkdn_rows WHERE number=%s", (number,))
            cursor.execute("DELETE FROM tkdn_checks WHERE number=%s", (number,))

        self._run(operation)

    def get_check(self, number: str) -> dict[str, Any] | None:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT c.number, c.status, c.checked_at, c.error_msg,
                           (SELECT COUNT(*) FROM tkdn_rows r WHERE r.number=c.number) AS row_count
                    FROM tkdn_checks c WHERE c.number=%s
                    """,
                    (number,),
                )
                return cursor.fetchone()
        finally:
            connection.close()

    def get_checks(self, numbers: Iterable[str]) -> list[dict[str, Any]]:
        values = list(numbers)
        if not values:
            return []
        placeholders = ", ".join(["%s"] * len(values))
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT c.number, c.status, c.checked_at, c.error_msg,
                           (SELECT COUNT(*) FROM tkdn_rows r WHERE r.number=c.number) AS row_count
                    FROM tkdn_checks c WHERE c.number IN ({placeholders})
                    """,
                    tuple(values),
                )
                return list(cursor.fetchall())
        finally:
            connection.close()

    def is_final(self, number: str) -> bool:
        check = self.get_check(number)
        if not check:
            return False
        status = check.get("status")
        row_count = int(check.get("row_count") or 0)
        if status == "found":
            return row_count > 0
        if status == "empty":
            return row_count == 0
        return False

    def search(
        self,
        q: str = "",
        number: str | None = None,
        brand: str | None = None,
        min_value: float | None = None,
        page: int = 1,
        per_page: int = 50,
        sort: str = "number",
        order: str = "asc",
    ) -> list[dict[str, Any]]:
        sort_columns = {
            "number": "number",
            "brand": "brand",
            "value": "value",
            "product_type": "product_type",
        }
        if sort not in sort_columns:
            raise ValueError(f"Unsupported sort column: {sort}")
        direction = "DESC" if str(order).lower() == "desc" else "ASC"
        clauses, params = self._filters(q=q, number=number, brand=brand, min_value=min_value)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        limit = max(1, int(per_page))
        offset = max(0, (int(page) - 1) * limit)
        sql = (
            "SELECT number, product_type, brand, type, description, standard, value, hs "
            f"FROM tkdn_rows{where} ORDER BY {sort_columns[sort]} {direction} "
            "LIMIT %s OFFSET %s"
        )
        params.extend([limit, offset])
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, tuple(params))
                return list(cursor.fetchall())
        finally:
            connection.close()

    def count(
        self,
        q: str = "",
        number: str | None = None,
        brand: str | None = None,
        min_value: float | None = None,
    ) -> int:
        clauses, params = self._filters(q=q, number=number, brand=brand, min_value=min_value)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) AS total FROM tkdn_rows{where}", tuple(params))
                row = cursor.fetchone() or {}
                return int(row.get("total") or 0)
        finally:
            connection.close()

    @staticmethod
    def _filters(
        *,
        q: str = "",
        number: str | None = None,
        brand: str | None = None,
        min_value: float | None = None,
    ) -> tuple[list[str], list[Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if number:
            clauses.append("number = %s")
            params.append(number)
        if q:
            clauses.append(
                "(LOWER(number) LIKE LOWER(%s) OR LOWER(brand) LIKE LOWER(%s) "
                "OR LOWER(type) LIKE LOWER(%s) OR LOWER(product_type) LIKE LOWER(%s) "
                "OR LOWER(description) LIKE LOWER(%s) OR LOWER(standard) LIKE LOWER(%s))"
            )
            like = f"%{q}%"
            params.extend([like] * 6)
        if brand:
            clauses.append("LOWER(brand) = LOWER(%s)")
            params.append(brand)
        if min_value is not None:
            clauses.append("value >= %s")
            params.append(min_value)
        return clauses, params


def row_hash(number: str, row: dict[str, Any]) -> str:
    parts = [
        number,
        row.get("specification_id") or "",
        row.get("brand") or "",
        row.get("type") or "",
        row.get("description") or "",
    ]
    return hashlib.sha256("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()
