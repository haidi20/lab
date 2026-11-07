from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable


class SQLiteOrderStore:
    def __init__(self, path: str | Path) -> None:
        self.connection = sqlite3.connect(str(path), check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self._initialize()

    def _initialize(self) -> None:
        with self.connection:
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    invoice TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS ledger_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    UNIQUE(invoice, event_type)
                )
                """
            )

    def save(self, order: dict[str, object]) -> None:
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO orders(invoice, payload, status) VALUES (?, ?, ?)
                ON CONFLICT(invoice) DO UPDATE SET payload = excluded.payload,
                    status = excluded.status, updated_at = CURRENT_TIMESTAMP
                """,
                (
                    str(order["invoice"]),
                    json.dumps(order, sort_keys=True),
                    str(order.get("status", "Pending")),
                ),
            )

    def find(self, invoice: str) -> dict[str, object]:
        row = self.connection.execute(
            "SELECT payload FROM orders WHERE invoice = ?", (invoice,)
        ).fetchone()
        if row is None:
            raise KeyError(f"Invoice tidak ditemukan: {invoice}")
        return dict(json.loads(row["payload"]))

    def find_all(self) -> list[dict[str, object]]:
        rows = self.connection.execute("SELECT payload FROM orders ORDER BY invoice").fetchall()
        return [dict(json.loads(row["payload"])) for row in rows]

    def ledger_entries(self, invoice: str) -> list[dict[str, object]]:
        rows = self.connection.execute(
            "SELECT invoice, event_type, amount FROM ledger_entries WHERE invoice = ? ORDER BY id",
            (invoice,),
        ).fetchall()
        return [dict(row) for row in rows]

    def record_ledger(self, invoice: str, event_type: str, amount: int) -> bool:
        try:
            with self.connection:
                self.connection.execute(
                    "INSERT INTO ledger_entries(invoice, event_type, amount) VALUES (?, ?, ?)",
                    (invoice, event_type, amount),
                )
            return True
        except sqlite3.IntegrityError:
            return False
