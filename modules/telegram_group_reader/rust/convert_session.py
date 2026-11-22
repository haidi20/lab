"""Konversi session Telethon (Python) ke schema SqliteSession grammers (Rust).

Dijalankan SEKALI:
    python convert_session.py

Membaca: telegram_group_reader.session (default, atau env TELEGRAM_SESSION)
Menulis: file yang sama (ditambah tabel dc_home/dc_option/...) agar Rust bisa baca.
"""
import os
import shutil
import sqlite3
from pathlib import Path

SOURCE = Path(os.environ.get("TELEGRAM_SESSION", "telegram_group_reader.session"))


def parse_server_address(value: str) -> tuple[str, int]:
    if ":" in value:
        host, _, port = value.rpartition(":")
        if host and port.isdigit():
            return host, int(port)
    # Telethon menyimpan hanya host, port ada di kolom terpisah.
    if value:
        return value, 0
    raise ValueError(f"Format server_address tidak valid: {value}")


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"Session tidak ditemukan: {SOURCE}. Jalankan Python dulu untuk login.")

    backup = SOURCE.with_suffix(".session.bak")
    if not backup.exists():
        shutil.copy2(SOURCE, backup)
        print(f"Backup dibuat: {backup}")

    con = sqlite3.connect(str(SOURCE))
    cur = con.cursor()
    row = cur.execute(
        "SELECT dc_id, server_address, port, auth_key FROM sessions LIMIT 1"
    ).fetchone()
    if not row:
        raise SystemExit("Tabel sessions kosong. Silakan login dengan Python dulu.")
    dc_id, server_address, port, auth_key = row
    host, parsed_port = parse_server_address(server_address)
    port = parsed_port or int(port)
    if auth_key is None or len(auth_key) != 256:
        raise SystemExit("auth_key tidak valid (harus 256 byte).")

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS dc_home (dc_id INTEGER NOT NULL, PRIMARY KEY(dc_id));
        CREATE TABLE IF NOT EXISTS dc_option (
            dc_id INTEGER NOT NULL, ipv4 TEXT NOT NULL, ipv6 TEXT NOT NULL,
            auth_key BLOB, PRIMARY KEY (dc_id));
        CREATE TABLE IF NOT EXISTS peer_info (
            peer_id INTEGER NOT NULL, hash INTEGER, subtype INTEGER, PRIMARY KEY (peer_id));
        CREATE TABLE IF NOT EXISTS update_state (
            pts INTEGER NOT NULL, qts INTEGER NOT NULL, date INTEGER NOT NULL, seq INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS channel_state (
            peer_id INTEGER NOT NULL, pts INTEGER NOT NULL, PRIMARY KEY (peer_id));
        """
    )
    cur.execute("DELETE FROM dc_home")
    cur.execute("INSERT INTO dc_home (dc_id) VALUES (?)", (dc_id,))
    cur.execute("DELETE FROM dc_option WHERE dc_id=?", (dc_id,))
    cur.execute(
        "INSERT INTO dc_option (dc_id, ipv4, ipv6, auth_key) VALUES (?, ?, ?, ?)",
        (dc_id, f"{host}:{port}", f"[::]:{port}", auth_key),
    )
    cur.execute("PRAGMA user_version = 1")
    con.commit()
    con.close()
    print(f"Session siap dipakai Rust: dc={dc_id}, host={host}:{port}")


if __name__ == "__main__":
    main()
