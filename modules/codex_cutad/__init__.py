"""Modul Codex CLI + gateway CutadAI.

Isi penting:

- `shim`          : proxy `127.0.0.1:8787` yang menulis ulang dua field yang
                    ditolak gateway (`developer -> system`, buang
                    `previous_response_id`) sambil meneruskan stream SSE.
- `config_codex`  : utilitas mengarahkan `~/.codex/config.toml` ke shim.
- `probe_model`   : probe `/v1/responses` per model sebelum config diubah.
- `switch_model`  : ganti model default (probe-gated, dengan backup).
- `fix_wire_api`  : perbaikan lama `wire_api = "responses" -> "chat"` (tidak
                    berlaku lagi: Codex 0.167.1 menolak mode chat).

Autostart shim di Windows: `start_shim.ps1`.
"""
import importlib

_shim = importlib.import_module("modules.codex_cutad.shim")


def __getattr__(nama: str):
    """Lazy import submodul (agar `python -m ...config_codex` tidak warning)."""
    if nama in ("config_codex", "fix_output_object"):
        modul = importlib.import_module("modules.codex_cutad." + nama)
        globals()[nama] = modul
        return modul
    raise AttributeError("module 'modules.codex_cutad' has no attribute %r" % nama)


shim = _shim
BASE_SHIM = "http://127.0.0.1:8787/v1"
bersihkan_payload = _shim.bersihkan_payload
buat_server = _shim.buat_server
normalisasi_baris_sse = _shim.normalisasi_baris_sse
ratakan_teks = _shim.ratakan_teks

__all__ = [
    "shim",
    "config_codex",
    "fix_output_object",
    "BASE_SHIM",
    "bersihkan_payload",
    "buat_server",
    "normalisasi_baris_sse",
    "ratakan_teks",
]

