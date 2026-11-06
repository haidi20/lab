"""Ekspos modul uptime_kuma.

Struktur:
- `uptime_kuma/` (folder ini) = clone github Uptime Kuma, server-nya jalan
  dari sini (npm start). Jangan jalankan npm install ulang kecuali perlu.
- check_cutad.py   : definisi monitor ai.cutad.web.id (spek di tests/)
- setup_monitors.py: daftar monitor ke server yang sedang jalan
- update_cutad_monitor.py: perbaiki monitor yang sudah ada (url/model/token)
"""
import importlib

_check = importlib.import_module("modules.uptime_kuma.check_cutad")
_update = importlib.import_module("modules.uptime_kuma.update_cutad_monitor")

MONITORS = _check.MONITORS
HASIL_PEMERIKSAAN_2026_11_06 = _check.HASIL_PEMERIKSAAN_2026_11_06
auth_headers = _check.auth_headers
monitors = _check.monitors
_api_key = _check._api_key

perbaiki_monitor = _update.perbaiki_monitor
TARGET_MONITOR = _update.TARGET

__all__ = [
    "MONITORS",
    "HASIL_PEMERIKSAAN_2026_11_06",
    "auth_headers",
    "monitors",
    "perbaiki_monitor",
    "TARGET_MONITOR",
]

