"""Daftarkan monitor ai.cutad.web.id ke Uptime Kuma yang sedang berjalan.

Dipakai setelah Uptime Kuma (server clone di folder ini) jalan:

    npm start                       # di folder ini, terminal lain
    python3 -m modules.uptime_kuma.setup_monitors

Kredensial hanya dari environment/.env:
    UPTIME_KUMA_URL      (default http://127.0.0.1:3001)
    UPTIME_KUMA_USERNAME
    UPTIME_KUMA_PASSWORD
    CUTAD_API_KEY        (token untuk header monitor)

Catatan: Uptime Kuma v3 punya REST API read-only (/api/monitors). Membuat
monitor dilakukan lewat socket.io: event `login` lalu event `add`.
"""
import json
import os
import sys

DEFAULT_URL = "http://127.0.0.1:3001"


def base_url():
    return os.environ.get("UPTIME_KUMA_URL", DEFAULT_URL).rstrip("/")


def kredensial():
    user = os.environ.get("UPTIME_KUMA_USERNAME", "").strip()
    password = os.environ.get("UPTIME_KUMA_PASSWORD", "")
    if not user or not password:
        raise RuntimeError(
            "UPTIME_KUMA_USERNAME dan UPTIME_KUMA_PASSWORD harus diisi di .env"
        )
    return user, password


def socket_payload(monitor):
    """Lengkapi definisi monitor dengan field wajib tabel monitor Uptime Kuma."""
    payload = {
        "name": monitor["name"],
        "type": monitor["type"],
        "parent": None,
        "description": monitor.get("description"),
        "active": True,
        "interval": monitor.get("interval", 60),
        "retryInterval": monitor.get("retryInterval", 60),
        "timeout": monitor.get("timeout", 48),
        "maxretries": monitor.get("maxretries", 0),
        "notificationIDList": {},
        "upsideDown": False,
        "accepted_statuscodes_json": json.dumps(
            monitor.get("accepted_statuscodes", ["200-299"])
        ),
        "conditions": json.dumps(monitor.get("conditions", [])),
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

    for kunci in ("url", "hostname", "keyword", "invertKeyword", "port", "dns_resolve_type"):
        if kunci in monitor:
            payload[kunci] = monitor[kunci]

    return payload


def daftarkan(socketio_klien, monitors):
    """Kirim tiap monitor lewat event `add`; kembalikan rekap hasil."""
    hasil = []
    for monitor in monitors:
        payload = socket_payload(monitor)
        jawaban = socketio_klien.emit("add", payload)
        ok = bool(isinstance(jawaban, dict) and jawaban.get("ok"))
        hasil.append(
            {
                "name": monitor["name"],
                "ok": ok,
                "msg": (jawaban or {}).get("msg", "tidak ada respons"),
            }
        )
    return hasil


def main():
    import socketio  # di-install via pip bila perlu

    kunci = os.environ.get("CUTAD_API_KEY", "").strip()
    if not kunci:
        raise RuntimeError("CUTAD_API_KEY tidak ada di .env")

    from modules.uptime_kuma.check_cutad import monitors as daftar_monitor

    user, password = kredensial()
    klien = socketio.Client()
    klien.connect(base_url(), wait_timeout=20)

    jawaban_login = klien.call("login", {"username": user, "password": password})
    if not jawaban_login or not jawaban_login.get("ok"):
        print(f"LOGIN GAGAL: {jawaban_login}")
        return 1

    print(f"LOGIN OK sebagai {user}")
    hasil = daftarkan(klien, daftar_monitor(kunci))
    klien.disconnect()

    for baris in hasil:
        tanda = "OK  " if baris["ok"] else "GAGAL"
        print(f"  {tanda} {baris['name']}: {baris['msg']}")

    return 0 if all(b["ok"] for b in hasil) else 1


if __name__ == "__main__":
    sys.exit(main())
