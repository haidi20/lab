"""Perbaiki jawaban Codex yang tampil sebagai `[object Object]...`.

Penyebab (diverifikasi 2026-11-24, 9router@0.5.119 `chunks/1297.js`):

- `~/.codex/config.toml` menunjuk 9router (`http://127.0.0.1:20128/v1`) dengan
  `model = "cd"` (combo). Combo meneruskan chunk reasoning ke
  `response.output_text.delta` sebagai **array objek**, padahal Responses API
  mewajibkan `delta` bertipe string. Codex memanggil `String(delta)` sehingga
  pengguna melihat `[object Object][object Object]...`.
- Gateway CutadAI langsung sehat: `POST /v1/responses` ke
  `https://ai.cutad.web.id/v1` mengembalikan `output_text.text` berupa string.
- `model = "cd"` hanya ada di 9router; model asli (`deepseek-v4-pro` dst.)
  harus dipakai bila provider diarahkan ke shim.

Perbaikan sisi klien: arahkan `base_url` provider `cutad` ke shim lokal
(`modules/codex_cutad/shim.py`, `127.0.0.1:8787`) dan ganti `model` combo
menjadi model asli. Shim menormalkan `delta` non-string sebelum diteruskan
(`shim.normalisasi_baris_sse`), jadi `[object Object]` tidak bisa muncul lagi
meskipun upstream tetap mengirim payload cacat.

Pakai:
    python -m modules.codex_cutad.fix_output_object --cek      # inspeksi
    python -m modules.codex_cutad.fix_output_object            # perbaiki
    python -m modules.codex_cutad.fix_output_object deepseek-v4-pro

Aturan anti upstream error tetap berlaku: model TIDAK ditulis sebelum probe
`/v1/responses` mengembalikan 200.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import time

from modules.codex_cutad import probe_model as probe

BASE_SHIM = "http://127.0.0.1:8787/v1"
MODEL_DEFAULT = "deepseek-v4-pro"
MODEL_COMBO = "cd"
PROVIDER = "cutad"
POLA_9ROUTER = re.compile(r"127\.0\.0\.1:201\d\d")


def path_config_default() -> str:
    """Path config default, bisa dioverride lewat env CODEX_CONFIG."""
    return os.environ.get("CODEX_CONFIG") or os.path.expanduser(
        "~/.codex/config.toml")


def _bagian_provider(isi: str):
    """Rentang baris tabel `[model_providers.cutad]`, atau None."""
    baris = isi.splitlines()
    awal = None
    for i, b in enumerate(baris):
        kandung = b.strip()
        if kandung.startswith("[") and not kandung.startswith("[["):
            if awal is not None:
                return awal, i
            if kandung.replace(" ", "") == "[model_providers.%s]" % PROVIDER:
                awal = i
    if awal is None:
        return None
    return awal, len(baris)


def base_url_dari_config(isi: str):
    """Nilai `base_url` pada tabel provider `cutad`, atau None."""
    rentang = _bagian_provider(isi)
    if rentang is None:
        return None
    awal, akhir = rentang
    for baris in isi.splitlines()[awal:akhir]:
        kandung = baris.strip()
        if kandung.startswith("base_url") and "=" in kandung:
            return kandung.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def lewat_9router(isi: str) -> bool:
    """True bila provider `cutad` menunjuk 9router (port 201xx)."""
    url = base_url_dari_config(isi) or ""
    return bool(POLA_9ROUTER.search(url))


def _ganti_top_level(isi: str, kunci: str, nilai_baru: str) -> list:
    """Ganti assignment top-level `kunci`; sisipkan bila belum ada."""
    baris = isi.splitlines()
    batas = len(baris)
    for i, b in enumerate(baris):
        if b.strip().startswith("["):
            batas = i
            break

    baris_baru = '%s = "%s"' % (kunci, nilai_baru)
    for i in range(batas):
        kandung = baris[i].strip()
        if kandung.startswith("#") or "=" not in kandung:
            continue
        if kandung.split("=", 1)[0].strip() == kunci:
            baris[i] = baris_baru
            return baris
    baris.insert(0, baris_baru)
    return baris


def ubah_ke_shim(isi: str, model: str = MODEL_DEFAULT) -> str:
    """Arahkan provider ke shim + ganti model combo menjadi model asli.

    Idempoten. Hanya menyentuh dua hal: assignment top-level `model` /
    `model_provider` dan baris `base_url` di tabel `[model_providers.cutad]`.
    Token, `wire_api`, tabel proyek, dan `[windows]` tidak diubah.
    """
    target = MODEL_DEFAULT if (model or MODEL_DEFAULT) == MODEL_COMBO \
        else (model or MODEL_DEFAULT)

    baris = _ganti_top_level(isi, "model", target)
    baris = _ganti_top_level("\n".join(baris), "model_provider", PROVIDER)

    rentang = _bagian_provider("\n".join(baris))
    if rentang is not None:
        awal, akhir = rentang
        baru = 'base_url = "%s"' % BASE_SHIM
        for i in range(awal, akhir):
            if baris[i].strip().startswith("base_url"):
                baris[i] = baru
                break
        else:
            baris.insert(awal + 1, baru)

    teks = "\n".join(baris)
    if isi.endswith("\n") and not teks.endswith("\n"):
        teks += "\n"
    return teks


def ganti_token(isi: str, token_baru: str) -> str:
    """Ganti `experimental_bearer_token` di tabel provider `cutad` (bila ada)."""
    rentang = _bagian_provider(isi)
    if rentang is None or not token_baru:
        return isi
    awal, akhir = rentang
    baris = isi.splitlines()
    for i in range(awal, akhir):
        if baris[i].strip().startswith("experimental_bearer_token"):
            baris[i] = 'experimental_bearer_token = "%s"' % token_baru
            teks = "\n".join(baris)
            if isi.endswith("\n") and not teks.endswith("\n"):
                teks += "\n"
            return teks
    return isi


def terapkan(path_config: str, backup_dir=None,
             target: str = MODEL_DEFAULT, token_baru: str | None = None) -> dict:
    """Terapkan perbaikan ke file; probe dulu, backup sebelum menulis.

    `token_baru` dipakai bila key 9router (gateway key) tidak berlaku di
    gateway tujuan - probe tetap wajib 200 sebelum file ditulis.
    """
    model = target or MODEL_DEFAULT
    with open(path_config, encoding="utf-8") as f:
        isi = f.read()

    baru = ubah_ke_shim(isi, model)
    token = token_baru or probe.token_dari_config(isi)
    if token_baru:
        baru = ganti_token(baru, token_baru)
    if baru == isi:
        return {"path": path_config, "status": "sudah-ok", "ke": model}

    url = probe.base_url_dari_config(isi)
    if not token:
        return {"path": path_config, "status": "token-kosong", "ke": model}

    hasil_probe = probe.kirim(probe.varian(model)["minimal"], token, url)
    if not hasil_probe.get("ok"):
        return {"path": path_config, "status": "probe-gagal", "ke": model,
                "status_http": hasil_probe.get("status"),
                "pesan": hasil_probe.get("teks")}

    folder = backup_dir or os.path.dirname(path_config) or "."
    stempel = time.strftime("%Y%m%d-%H%M%S")
    cadangan = os.path.join(
        folder, "%s.bak-%s-9router" % (os.path.basename(path_config), stempel))
    shutil.copy2(path_config, cadangan)

    with open(path_config, "w", encoding="utf-8", newline="\n") as f:
        f.write(baru)
    return {"path": path_config, "status": "fixed", "ke": model,
            "base_url": BASE_SHIM, "backup": cadangan,
            "probe": hasil_probe.get("teks")}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Perbaiki jawaban Codex '[object Object]' (9router -> shim)")
    parser.add_argument("model", nargs="?", default=MODEL_DEFAULT)
    parser.add_argument("--cek", action="store_true", help="hanya periksa")
    parser.add_argument("--path", default=None, help="config.toml alternatif")
    parser.add_argument("--token", default=None,
                        help="bearer token gateway tujuan (default: isi config "
                             "atau env CODEX_CUTAD_TOKEN)")
    args = parser.parse_args(argv)

    target = args.path or path_config_default()
    with open(target, encoding="utf-8") as f:
        isi = f.read()

    if args.cek:
        if lewat_9router(isi):
            print("%s: lewat 9router (%s) -> sumber '[object Object]'"
                  % (target, base_url_dari_config(isi)))
            return 1
        print("%s: base_url %s (bukan 9router)"
              % (target, base_url_dari_config(isi)))
        return 0

    hasil = terapkan(target, target=args.model,
                     token_baru=args.token or os.environ.get("CODEX_CUTAD_TOKEN"))
    status = hasil["status"]
    if status == "sudah-ok":
        print("sudah-ok: %s (model %s, base_url %s)"
              % (target, hasil["ke"], BASE_SHIM))
        return 0
    if status != "fixed":
        print("%s: %s %s" % (status, hasil.get("status_http"),
                             hasil.get("pesan")))
        return 3
    print("fixed: %s -> model %s via %s (backup %s)"
          % (target, hasil["ke"], BASE_SHIM,
             os.path.basename(hasil["backup"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
