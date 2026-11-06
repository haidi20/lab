"""Daftarkan 3 monitor AI model ai.cutad.web.id ke Uptime Kuma.

Monitor bertipe `keyword` yang POST ke /v1/chat/completions dengan pesan
"hallo"; monitor UP bila respons mengandung kata "hallo"/"Hallo".

Dipakai setelah Uptime Kuma (server clone di folder ini) jalan:

    npm start                       # di folder ini, terminal lain
    python3 -m modules.uptime_kuma.setup_ai_model_monitors

Kredensial hanya dari environment/.env:
    UPTIME_KUMA_URL      (default http://127.0.0.1:3001)
    UPTIME_KUMA_USERNAME / UPTIME_KUMA_PASSWORD
    CUTAD_API_KEY        (token untuk header monitor)
"""
import json
import os
import sys

URL_CHAT = "https://ai.cutad.web.id/v1/chat/completions"
# Keyword di-scan case-sensitive oleh Uptime Kuma (data.includes), sementara
# model cenderung membalas "Hallo"/"Halo" bila cuma ditanya "hallo".
# Prompt ini terbukti membuat ketiga model membalas persis 'hallo' lowercase.
KEYWORD = "hallo"
PESAN = "balas persis tanpa mengubah huruf apapun: hallo"

# 3 model AI (url, key, dan ref model dari file py di tests/):
MODELS = ["z-ai/glm-5.2", "glm-5.3-flash", "deepseek-v4-pro"]


def _api_key():
    kunci = os.environ.get("CUTAD_API_KEY", "").strip()
    if not kunci:
        raise RuntimeError(
            "CUTAD_API_KEY tidak ada di environment. Isi di .env: CUTAD_API_KEY=<token cutad>"
        )
    return kunci


def auth_headers(api_key):
    """Header Authorization + Content-Type, konsisten dengan check_cutad.py."""
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def monitor_model(model, api_key=None):
    """Definisi 1 monitor keyword utk 1 model AI (body berupa dict)."""
    if api_key is None:
        api_key = _api_key()
    return {
        "name": f"{model} via chat/completions (hallo)",
        "type": "keyword",
        "url": URL_CHAT,
        "method": "POST",
        "body": {
            "model": model,
            "messages": [{"role": "user", "content": PESAN}],
        },
        "keyword": KEYWORD,
        "invertKeyword": False,
        "headers": auth_headers(api_key),
        "accepted_statuscodes": ["200-299"],
        "interval": 300,
    }


def monitors(api_key=None):
    """3 monitor (satu per model)."""
    kunci = api_key if api_key is not None else _api_key()
    return [monitor_model(model, kunci) for model in MODELS]


def socket_payload(monitor):
    """Lengkapi definisi monitor dengan field wajib tabel monitor Uptime Kuma.

    Konsisten dengan setup_monitors.socket_payload: body dict -> string JSON.
    """
    payload = {
        "name": monitor["name"],
        "type": monitor["type"],
        "parent": None,
        "description": monitor.get("description"),
        "active": True,
        "interval": monitor.get("interval", 300),
        "retryInterval": monitor.get("retryInterval", 60),
        "timeout": monitor.get("timeout", 48),
        "maxretries": monitor.get("maxretries", 0),
        "notificationIDList": {},
        "upsideDown": False,
        # Kuma v3 handler `add` menerima array dan men-JSON-kan sendiri
        # (accepted_statuscodes_json disusun di server).
        "accepted_statuscodes": monitor.get("accepted_statuscodes", ["200-299"]),
        "conditions": monitor.get("conditions", []),
        "resendInterval": 0,
        "method": monitor.get("method", "GET"),
        "headers": json.dumps(monitor.get("headers") or {}),
        "body": monitor.get("body", ""),
        "httpBodyEncoding": "json",
        "maxredirects": 10,
        "ipFamily": None,
    }

    if isinstance(payload["body"], (dict, list)):
        payload["body"] = json.dumps(payload["body"])

    for kunci in ("url", "hostname", "keyword", "invertKeyword", "port"):
        if kunci in monitor:
            payload[kunci] = monitor[kunci]

    return payload


def ambil_id_monitor(db_connection, nama_monitor):
    """Ambil id monitor dari DB yang namanya ada di daftar nama_monitor."""
    if not nama_monitor:
        return []
    placeholder = ",".join("?" for _ in nama_monitor)
    rows = db_connection.execute(
        f"select id from monitor where name in ({placeholder})",
        list(nama_monitor),
    ).fetchall()
    return [row[0] for row in rows]


def hapus_monitor(socketio_klien, monitor_id, timeout=20):
    """Hapus 1 monitor via event `deleteMonitor`; kembalikan hasil terstruktur."""
    wadah = {}

    def terima(jawaban):
        wadah["jawaban"] = jawaban

    socketio_klien.emit("deleteMonitor", monitor_id, False, callback=terima)
    if hasattr(socketio_klien, "sleep"):
        for _ in range(timeout * 2):
            if wadah.get("jawaban") is not None:
                break
            socketio_klien.sleep(0.5)

    jawaban = wadah.get("jawaban")
    ok = bool(isinstance(jawaban, dict) and jawaban.get("ok"))
    return {
        "id": monitor_id,
        "ok": ok,
        "msg": (jawaban or {}).get("msg", "tidak ada respons"),
    }


def daftarkan(socketio_klien, monitors):
    """Kirim tiap monitor lewat event `add`; kembalikan rekap hasil.

    Ack socket.io ditangkap lewat callback (python-socketio tidak
    mengembalikan nilai `emit`).
    """
    hasil = []
    for monitor in monitors:
        payload = socket_payload(monitor)
        wadah = {}

        def terima(jawaban):
            wadah["jawaban"] = jawaban

        socketio_klien.emit("add", payload, callback=terima)
        # Server Kuma v3 await startMonitor() SEBELUM callback `add` dipanggil,
        # jadi ack bisa lambat (cek pertama = POST ke LLM, bisa >10 detik).
        if hasattr(socketio_klien, "sleep"):
            for _ in range(150):  # maksimal 75 detik
                if wadah.get("jawaban") is not None:
                    break
                socketio_klien.sleep(0.5)

        jawaban = wadah.get("jawaban")
        ok = bool(isinstance(jawaban, dict) and jawaban.get("ok"))
        hasil.append(
            {
                "name": monitor["name"],
                "ok": ok,
                "msg": (jawaban or {}).get("msg", "tidak ada respons"),
            }
        )
    return hasil


def sign_in_cookie(base_url, username, password, timeout=15):
    """Login lewat HTTP better-auth, kembalikan string cookie sesi (atau None).

    Socket.io Uptime Kuma v3 mengambil sesi dari header `Cookie`,
    endpoint: /api/auth/sign-in/username.
    """
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


def kredensial():
    user = os.environ.get("UPTIME_KUMA_USERNAME", "").strip()
    password = os.environ.get("UPTIME_KUMA_PASSWORD", "")
    if not user or not password:
        raise RuntimeError(
            "UPTIME_KUMA_USERNAME dan UPTIME_KUMA_PASSWORD harus diisi di .env"
        )
    return user, password


def base_url():
    return os.environ.get("UPTIME_KUMA_URL", "http://127.0.0.1:3001").rstrip("/")


def main():
    import socketio  # di-install via pip bila perlu
    import sqlite3

    api_key = _api_key()
    user, password = kredensial()
    base = base_url()

    cookie = sign_in_cookie(base, user, password)
    if not cookie:
        print("Login gagal: tidak dapat cookie sesi")
        return 1
    print(f"LOGIN OK sebagai {user}")

    klien = socketio.Client()
    klien.connect(base, wait_timeout=20, headers={"Cookie": cookie})

    daftar = monitors(api_key)

    # Idempoten: bersihkan monitor lama dengan nama sama sebelum daftar ulang.
    db_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data", "kuma.db"
    )
    koneksi = sqlite3.connect(db_path)
    try:
        ids_lama = ambil_id_monitor(koneksi, [m["name"] for m in daftar])
        for monitor_id in ids_lama:
            hasil_hapus = hapus_monitor(klien, monitor_id)
            tanda = "OK  " if hasil_hapus["ok"] else "GAGAL"
            print(f"  {tanda} hapus monitor lama #{monitor_id}: {hasil_hapus['msg']}")
    finally:
        koneksi.close()

    hasil = daftarkan(klien, daftar)
    klien.disconnect()

    for baris in hasil:
        tanda = "OK  " if baris["ok"] else "GAGAL"
        print(f"  {tanda} {baris['name']}: {baris['msg']}")

    return 0 if all(b["ok"] for b in hasil) else 1


if __name__ == "__main__":
    sys.exit(main())