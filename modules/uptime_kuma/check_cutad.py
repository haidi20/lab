"""Definisi monitor Uptime Kuma untuk ai.cutad.web.id.

Token API hanya dibaca dari environment (CUTAD_API_KEY / .env) —
tidak pernah di-hardcode di sini. File ini TIDAK menjalankan server;
server Uptime Kuma tetap sumber clone github di folder modul ini.
"""
import json
import os


def _api_key():
    kunci = os.environ.get("CUTAD_API_KEY", "").strip()
    if not kunci:
        raise RuntimeError(
            "CUTAD_API_KEY tidak ada di environment. "
            "Isi di .env: CUTAD_API_KEY=<token cutad>"
        )
    return kunci


def auth_headers(api_key):
    """Header Authorization + Content-Type untuk request ke ai.cutad.web.id."""
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def monitors(api_key=None):
    """Daftar monitor (format Uptime Kuma via socket API).

    Catatan desain:
    - field `body` sengaja berupa **dict** (bukan string JSON) supaya enak
      dites dan di-import; saat mendaftarkan ke Uptime Kuma, script setup
      yang meng-serialize ke JSON (API socket Uptime Kuma menerima string).
    - token hanya lewat env; header dibuat lewat auth_headers().
    """
    kunci = api_key if api_key is not None else _api_key()
    headers = auth_headers(kunci)

    return [
        {
            "name": "Ping jaringan ke ai.cutad.web.id",
            "type": "ping",
            "hostname": "ai.cutad.web.id",
            "interval": 60,
        },
        {
            "name": "API key & koneksi HTTPS ai.cutad.web.id",
            "type": "http",
            "url": "https://ai.cutad.web.id",
            "method": "GET",
            "httpFormat": "any-valid-status",
            "headers": dict(headers),
            "accepted_statuscodes": ["200-299"],
            "interval": 120,
        },
        {
            "name": "z-ai/glm-5.2 via chat/completions",
            "type": "keyword",
            "url": "https://ai.cutad.web.id/v1/chat/completions",
            "method": "POST",
            "body": {
                "model": "z-ai/glm-5.2",
                "messages": [{"role": "user", "content": "balas PONG saja"}],
            },
            "keyword": "PONG",
            "invertKeyword": False,
            "headers": dict(headers),
            "interval": 300,
        },
        {
            "name": "z-ai/glm-5.2 via responses (jalur Codex)",
            "type": "keyword",
            "url": "https://ai.cutad.web.id/v1/responses",
            "method": "POST",
            "body": {
                "model": "z-ai/glm-5.2",
                "input": "balas PONG saja",
            },
            "keyword": "PONG",
            "invertKeyword": False,
            "headers": dict(headers),
            "interval": 300,
        },
        {
            "name": "glm-5.3-flash via chat/completions",
            "type": "keyword",
            "url": "https://ai.cutad.web.id/v1/chat/completions",
            "method": "POST",
            "body": {
                "model": "glm-5.3-flash",
                "messages": [{"role": "user", "content": "balas PONG saja"}],
            },
            "keyword": "PONG",
            "invertKeyword": False,
            "headers": dict(headers),
            "interval": 300,
        },
        {
            "name": "glm-5.3-flash / deepseek-v4-pro via Codex",
            "type": "keyword",
            "url": "https://ai.cutad.web.id/v1/responses",
            "method": "POST",
            "body": {
                "model": "glm-5.3-flash",
                "input": "balas PONG saja",
            },
            "keyword": "PONG",
            "invertKeyword": False,
            "headers": dict(headers),
            "interval": 300,
        },
    ]


MONITORS = monitors()


# Rekap hasil pemeriksaan manual 2026-11-06 (sumber: user)
HASIL_PEMERIKSAAN_2026_11_06 = [
    {
        "item": "Ping jaringan ke ai.cutad.web.id",
        "status": "ok",
        "detail": "✅ 47 ms rata-rata, 0% packet loss",
    },
    {
        "item": "API key & koneksi HTTPS",
        "status": "ok",
        "detail": "✅ Valid (bukan masalah auth)",
    },
    {
        "item": "z-ai/glm-5.2 via chat/completions",
        "status": "gagal",
        "detail": "❌ upstream_error",
    },
    {
        "item": "z-ai/glm-5.2 via responses (jalur Codex)",
        "status": "gagal",
        "detail": "❌ upstream_error",
    },
    {
        "item": "glm-5.3-flash via chat/completions",
        "status": "ok",
        "detail": "✅ Jalan! jawab PONG (86 tokens)",
    },
    {
        "item": "glm-5.3-flash / deepseek-v4-pro via Codex",
        "status": "gagal",
        "detail": "❌ unsupported_parameter (Codex kirim parameter reasoning yang proxy tolak utk model ini)",
    },
]
