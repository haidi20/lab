"""Perbaiki monitor 'cutad - glm 5.2' yang sudah terdaftar di Uptime Kuma.

Monitor lama terlanjur dibuat dengan URL salah (`https://ai.cutad.com`,
method GET) tanpa token. Script ini memperbaikinya sesuai spek di
`tests/test_check_cutad.py`:

    type   : keyword
    url    : https://ai.cutad.web.id/v1/chat/completions
    method : POST
    model  : z-ai/glm-5.2
    keyword: PONG
    header : Authorization: Bearer $CUTAD_API_KEY

Pakai:
    python3 -m modules.uptime_kuma.update_cutad_monitor
"""
import json
import os
import sys

TARGET = {
    "type": "keyword",
    "url": "https://ai.cutad.web.id/v1/chat/completions",
    "method": "POST",
    "body": {
        "model": "z-ai/glm-5.2",
        "messages": [{"role": "user", "content": "balas PONG saja"}],
    },
    "keyword": "PONG",
    "invertKeyword": False,
    "accepted_statuscodes": ["200-299"],
    "interval": 300,
}

NAMA_MONITOR = "cutad - glm 5.2"


def _api_key():
    kunci = os.environ.get("CUTAD_API_KEY", "").strip()
    if not kunci:
        raise RuntimeError("CUTAD_API_KEY tidak ada di .env")
    return kunci


def payload_update(monitor_db, api_key):
    """Bangun payload `editMonitor` dari record monitor di DB + spek TARGET."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    return {
        "id": monitor_db["id"],
        "name": monitor_db.get("name") or NAMA_MONITOR,
        "type": TARGET["type"],
        "url": TARGET["url"],
        "method": TARGET["method"],
        "body": json.dumps(TARGET["body"]),
        "headers": json.dumps(headers),
        "keyword": TARGET["keyword"],
        "invertKeyword": TARGET["invertKeyword"],
        "accepted_statuscodes_json": json.dumps(TARGET["accepted_statuscodes"]),
        "conditions": json.dumps([]),
        "interval": TARGET["interval"],
        "retryInterval": 60,
        "timeout": 48,
        "maxretries": 0,
        "active": True,
        "parent": None,
        "notificationIDList": {},
        "description": None,
        "upsideDown": False,
        "resendInterval": 0,
        "httpBodyEncoding": "json",
        "maxredirects": 10,
        "ipFamily": None,
    }


def perbaiki_monitor(socketio_klien, monitor_db, api_key, timeout=20):
    """Kirim `editMonitor` untuk satu monitor; kembalikan hasil terstruktur.

    Ack socket.io ditangkap lewat callback (python-socketio tidak
    mengembalikan nilai `emit`, jadi tanpa callback jawabannya selalu hilang).
    """
    payload = payload_update(monitor_db, api_key)
    wadah = {}

    def terima(jawaban):
        wadah["jawaban"] = jawaban

    socketio_klien.emit("editMonitor", payload, terima)
    socketio_klien.sleep(timeout / 2) if hasattr(socketio_klien, "sleep") else None

    jawaban = wadah.get("jawaban")
    ok = bool(isinstance(jawaban, dict) and jawaban.get("ok"))
    return {
        "id": monitor_db.get("id"),
        "name": payload["name"],
        "ok": ok,
        "msg": (jawaban or {}).get("msg", "tidak ada respons"),
        "url": payload["url"],
        "model": TARGET["body"]["model"],
    }


def sign_in_cookie(base_url, username, password, timeout=15):
    """Login lewat HTTP better-auth, kembalikan string cookie sesi (atau None).

    Socket.io Uptime Kuma v3 mengambil sesi dari header `Cookie`, jadi login
    tidak lagi lewat event `login`. Endpoint: /api/auth/sign-in/username
    """
    import json
    import urllib.error
    import urllib.request

    permintaan = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/auth/sign-in/username",
        data=json.dumps({"username": username, "password": password}).encode(),
        headers={"Content-Type": "application/json", "Origin": base_url},
    )

    try:
        with urllib.request.urlopen(permintaan, timeout=timeout) as respons:
            cookie_header = respons.headers.get("set-cookie") or ""
    except (urllib.error.URLError, OSError):
        return None

    for bagian in cookie_header.split(","):
        bagian = bagian.strip()
        if bagian.startswith("better-auth.session_token="):
            return bagian.split(";")[0]
    return None


def ambil_monitor(db_path, nama=NAMA_MONITOR):
    """Ambil record monitor dari kuma.db (dipakai CLI)."""
    import sqlite3

    koneksi = sqlite3.connect(db_path)
    koneksi.row_factory = sqlite3.Row
    baris = koneksi.execute(
        "select id, name, type, url, method, body, headers, keyword from monitor where name = ?",
        (nama,),
    ).fetchone()
    koneksi.close()
    return dict(baris) if baris else None


def main():
    import socketio

    from modules.uptime_kuma.setup_monitors import base_url, kredensial

    api_key = _api_key()
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "kuma.db")

    monitor_db = ambil_monitor(db_path)
    if not monitor_db:
        print(f"Monitor '{NAMA_MONITOR}' tidak ditemukan di {db_path}")
        return 1

    user, password = kredensial()
    base = base_url()
    cookie = sign_in_cookie(base, user, password)
    if not cookie:
        print("Login gagal: tidak dapat cookie sesi")
        return 1

    klien = socketio.Client()
    klien.connect(base, wait_timeout=20, headers={"Cookie": cookie})

    hasil = perbaiki_monitor(klien, monitor_db, api_key)
    klien.disconnect()

    tanda = "OK  " if hasil["ok"] else "GAGAL"
    print(f"{tanda} [{hasil['id']}] {hasil['name']} -> {hasil['url']} ({hasil['model']})")
    print(f"     {hasil['msg']}")
    return 0 if hasil["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
