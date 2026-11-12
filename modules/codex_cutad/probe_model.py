"""Probe end-to-end model CutadAI lewat /v1/responses (jalur Codex 0.167).

Kenapa ada (temuan 2026-11-12):
- `deepseek-v4-pro` ADA di `/v1/models` gateway CutadAI.
- Gateway mengembalikan error JSON
  ``{"error":{"code":"11128","message":"Upstream error. Contact support if
  this persists."}}`` bila payload memuat sesuatu yang tidak didukung. Untuk
  `tencent/hy4-preview` pemicunya ``role:"developer"``; untuk model lain
  pemicunya perlu dibuktikan per-model.
- Probe ini dipakai untuk memilih kombinasi payload yang 200 SEBELUM config
  Codex diubah, supaya switch model tidak berakhir "Upstream error".

Payload kecil (tanpa tools) dipakai supaya hasilnya menunjukkan dukungan
gateway per model, bukan sekadar soal kuota/ukuran.

Pakai::

    python -m modules.codex_cutad.probe_model deepseek-v4-pro
    python -m modules.codex_cutad.probe_model deepseek-v4-pro --semua-varian

Config default: ~/.codex/config.toml (override: env CODEX_CONFIG).
Token dibaca dari `experimental_bearer_token` di config tersebut; tidak
pernah ditulis ke log.
"""
from __future__ import annotations

import gzip
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
import zlib
from pathlib import Path

URL_DEFAULT = "https://ai.cutad.web.id/v1/responses"

# Gateway memakai chain Let's Encrypt (leaf valid s/d 2027). Sertifikat yang
# sudah kedaluwarsa di mesin ini adalah ROOT lama "ISRG Root X1 (2015)" yang
# tertinggal di store Windows; Python 3.10 Windows memakai store itu sehingga
# error "_ssl.c:997 certificate has expired" walau chain sebenarnya OK (curl
# Windows memberi ssl_verify=0). Certifi selalu membawa root baru, jadi probe
# memprioritaskan certifi dan hanya jatuh ke store OS bila certifi absen.
def ssl_context():
    """Konteks TLS: certifi > store OS > tanpa verifikasi (probe saja)."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:  # noqa: BLE001 - certifi tidak terpasang
        pass
    try:
        return ssl.create_default_context()
    except Exception:  # noqa: BLE001 - store OS rusak
        return ssl._create_unverified_context()


SSL_CTX = ssl_context()


TEKS_PROBE = "Balas hanya satu kata: PONG"


def path_config_default() -> str:
    """Path config Codex default, bisa dioverride lewat env CODEX_CONFIG."""
    return os.environ.get("CODEX_CONFIG") or str(
        Path.home() / ".codex" / "config.toml"
    )


def token_dari_config(isi: str):
    """Ambil `experimental_bearer_token` pertama dari isi config TOML."""
    for baris in isi.splitlines():
        kandung = baris.strip()
        if kandung.startswith("experimental_bearer_token") and "=" in kandung:
            nilai = kandung.split("=", 1)[1].strip().strip('"').strip("'")
            return nilai or None
    return None


def base_url_dari_config(isi: str, provider: str = "cutad-direct") -> str:
    """base_url tabel `[model_providers.<provider>]` (fallback: gateway cutad)."""
    aktif = False
    for baris in isi.splitlines():
        kandung = baris.strip()
        if kandung.startswith("["):
            aktif = kandung.rstrip("]").strip() == "model_providers." + provider
            continue
        if aktif and kandung.startswith("base_url") and "=" in kandung:
            nilai = kandung.split("=", 1)[1].strip().strip('"').strip("'")
            if nilai:
                return nilai.rstrip("/") + "/responses"
    return URL_DEFAULT



def _pesan(teks: str, role: str = "user") -> dict:
    return {
        "type": "message",
        "role": role,
        "content": [{"type": "input_text", "text": teks}],
    }


def varian(model: str) -> dict:
    """Payload yang diuji, dari paling minimal ke paling mirip Codex.

    `minimal`   = bukti gateway menerima model (setara curl biasa).
    `developer` = apa yang selalu dikirim Codex 0.167 (role instruksi).
    `codex-ish` = developer + reasoning effort low, tetap tanpa tool.
    """
    dasar = {
        "model": model,
        "stream": True,
        "store": False,
        "input": [_pesan(TEKS_PROBE)],
    }
    dev = {
        "model": model,
        "stream": True,
        "store": False,
        "input": [_pesan("Kamu asisten uji.", "developer"), _pesan(TEKS_PROBE)],
    }
    codex_ish = {
        "model": model,
        "stream": True,
        "store": False,
        "reasoning": {"effort": "low", "summary": "auto"},
        "input": [_pesan("Kamu asisten uji.", "developer"), _pesan(TEKS_PROBE)],
    }
    return {"minimal": dasar, "developer": dev, "codex-ish": codex_ish}


def ringkas_balasan(isi: str) -> str:
    """Ambil potongan teks balasan (SSE `data: {...}` atau JSON biasa)."""
    potongan = []
    for baris in isi.splitlines():
        kandung = baris.strip()
        if kandung.startswith("data:"):
            kandung = kandung[5:].strip()
        if not kandung.startswith("{"):
            continue
        try:
            data = json.loads(kandung)
        except ValueError:
            continue
        if not isinstance(data, dict):
            continue
        if data.get("type") == "response.output_text.delta":
            potongan.append(str(data.get("delta", "")))
            continue
        if isinstance(data.get("output_text"), str):
            potongan.append(data["output_text"])
        for item in data.get("output") or []:
            for bagian in (item or {}).get("content") or []:
                if isinstance(bagian.get("text"), str):
                    potongan.append(bagian["text"])
        if "error" in data:
            return "ERROR " + json.dumps(data["error"], ensure_ascii=False)[:160]
    teks = "".join(potongan).strip()
    return teks[:160] if teks else "(tanpa teks)"



def _decode(body: bytes, encoding: str) -> str:
    """Decode body respons; gateway kadang menandai gzip walau tidak di-gzip."""
    if encoding and "gzip" in encoding.lower():
        try:
            body = gzip.decompress(body)
        except OSError:
            pass
    elif encoding and "deflate" in encoding.lower():
        try:
            body = zlib.decompress(body)
        except zlib.error:
            pass
    return body.decode("utf-8", "replace")


def _kode_error(teks: str):
    """Ambil `error.code` dari body error JSON (mis. '11128')."""
    try:
        data = json.loads(teks)
    except ValueError:
        return None
    if isinstance(data, dict) and isinstance(data.get("error"), dict):
        kode = data["error"].get("code")
        return str(kode) if kode is not None else None
    return None


def kirim(payload: dict, token: str, url: str = URL_DEFAULT,
          timeout: int = 90) -> dict:
    """POST payload ke gateway; kembalikan status/kode/potongan teks."""
    data = json.dumps(payload, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX)
    except urllib.error.HTTPError as exc:
        teks = _decode(exc.read(), exc.headers.get("Content-Encoding", ""))
        return {
            "status": exc.code,
            "kode": _kode_error(teks),
            "teks": _kode_error(teks) or teks[:160],
            "ok": False,
        }
    except Exception as exc:  # noqa: BLE001 - gangguan jaringan apa pun
        return {"status": 0, "kode": None, "teks": repr(exc), "ok": False}

    encoding = resp.headers.get("Content-Encoding", "")
    with resp:
        teks = _decode(resp.read(), encoding)
    return {
        "status": getattr(resp, "status", 200),
        "kode": None,
        "teks": ringkas_balasan(teks),
        "ok": True,
    }


def pilih_varian(hasil: dict):
    """Nama varian pertama yang 200, atau None bila semuanya gagal."""
    for nama, info in hasil.items():
        if info.get("ok"):
            return nama
    return None


def main() -> int:
    argumen = list(sys.argv[1:])
    if not argumen:
        print("pakai: python -m modules.codex_cutad.probe_model <model> "
              "[--semua-varian]")
        return 2
    model = argumen[0]
    semua = "--semua-varian" in argumen

    path = path_config_default()
    if not os.path.exists(path):
        print("Config tidak ditemukan: " + path)
        return 1
    isi = Path(path).read_text(encoding="utf-8")
    token = token_dari_config(isi)
    if not token:
        print("Token tidak ditemukan di " + path)
        return 1
    url = base_url_dari_config(isi)

    payloads = varian(model)
    urutan = list(payloads) if semua else ["minimal"]
    hasil = {}
    for nama in urutan:
        info = kirim(payloads[nama], token, url)
        hasil[nama] = info
        print("%-11s -> %s %s" % (nama, info["status"], info["teks"]))
        if info.get("ok") and not semua:
            break

    menang = pilih_varian(hasil)
    print("varian-ok: " + (menang or "-"))
    return 0 if menang else 3


if __name__ == "__main__":
    sys.exit(main())

