from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable


class SQLiteOrderStore:
    def __init__(self, path: str | Path) -> None:
        self.connection = sqlite3.connect(str(path), check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA busy_timeout = 5000")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.execute("PRAGMA synchronous = NORMAL")
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
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS bot_states (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS deposit_tickets (
                    ticket_no TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS webhook_events (
                    event_key TEXT PRIMARY KEY,
                    invoice TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL,
                    received_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice TEXT NOT NULL,
                    action TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(invoice, action, status, message)
                )
                """
            )
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS update_errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    update_id INTEGER NOT NULL,
                    error TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(update_id, error, payload)
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

    def save_deposit(self, deposit: dict[str, object]) -> None:
        ticket_no = str(deposit.get("notes", ""))
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO deposit_tickets(ticket_no, payload, status) VALUES (?, ?, ?)
                ON CONFLICT(ticket_no) DO UPDATE SET payload = excluded.payload,
                    status = excluded.status, updated_at = CURRENT_TIMESTAMP
                """,
                (ticket_no, json.dumps(deposit, sort_keys=True), str(deposit.get("status", "Pending"))),
            )

    def find_deposit(self, ticket_no: str) -> dict[str, object]:
        row = self.connection.execute(
            "SELECT payload FROM deposit_tickets WHERE ticket_no = ?", (ticket_no,)
        ).fetchone()
        if row is None:
            raise KeyError(f"Tiket deposit tidak ditemukan: {ticket_no}")
        return json.loads(row["payload"])

    def record_webhook(self, payload: dict[str, object]) -> bool:
        invoice = str(payload.get("ref_id", ""))
        status = str(payload.get("status", ""))
        message = str(payload.get("message", ""))
        event_key = f"{invoice}:{status}:{message}"
        try:
            with self.connection:
                self.connection.execute(
                    "INSERT INTO webhook_events(event_key, invoice, payload, status) VALUES (?, ?, ?, ?)",
                    (event_key, invoice, json.dumps(payload, sort_keys=True), status),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def webhook_events(self) -> list[dict[str, object]]:
        rows = self.connection.execute(
            "SELECT event_key, invoice, payload, status FROM webhook_events ORDER BY received_at, event_key"
        ).fetchall()
        return [
            {
                "event_key": row["event_key"],
                "invoice": row["invoice"],
                "payload": json.loads(row["payload"]),
                "status": row["status"],
            }
            for row in rows
        ]

    def record_audit(self, invoice: str, action: str, status: str, message: str) -> bool:
        try:
            with self.connection:
                self.connection.execute(
                    "INSERT INTO audit_logs(invoice, action, status, message) VALUES (?, ?, ?, ?)",
                    (invoice, action, status, message),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def audit_logs(self) -> list[dict[str, object]]:
        rows = self.connection.execute(
            "SELECT invoice, action, status, message FROM audit_logs ORDER BY id"
        ).fetchall()
        return [dict(row) for row in rows]

    def record_update_error(self, update_id: int, error: str, payload: object) -> bool:
        serialized_payload = json.dumps(payload, sort_keys=True, default=str)
        try:
            with self.connection:
                self.connection.execute(
                    "INSERT INTO update_errors(update_id, error, payload) VALUES (?, ?, ?)",
                    (update_id, error, serialized_payload),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def update_errors(self) -> list[dict[str, object]]:
        rows = self.connection.execute(
            "SELECT update_id, error, payload FROM update_errors ORDER BY id"
        ).fetchall()
        return [
            {
                "update_id": row["update_id"],
                "error": row["error"],
                "payload": json.loads(row["payload"]),
            }
            for row in rows
        ]

    def get_update_offset(self) -> int:
        row = self.connection.execute(
            "SELECT value FROM bot_states WHERE key = 'update_offset'"
        ).fetchone()
        return int(row["value"]) if row else 0

    def set_update_offset(self, value: int) -> None:
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO bot_states(key, value) VALUES ('update_offset', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (str(int(value)),),
            )
