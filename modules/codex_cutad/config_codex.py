"""Utilitas config Codex: arahkan `~/.codex/config.toml` ke shim lokal.

Gateway `ai.cutad.web.id` menolak dua field yang selalu dikirim Codex 0.167.1
(`role:"developer"` dan `previous_response_id`), jadi `base_url` provider
`cutad` harus menunjuk shim `modules/codex_cutad/shim.py`, bukan gateway.

Fungsi di sini murni string->string (mudah diuji TDD); penulisan file dan
backup dilakukan `terapkan`.

    python -m modules.codex_cutad.config_codex --cek     # inspeksi
    python -m modules.codex_cutad.config_codex           # perbaiki + backup
"""
from __future__ import annotations

import argparse
import datetime as _dt
import os
import shutil
import sys

PORT = 8787
BASE_SHIM = "http://127.0.0.1:%d/v1" % PORT
BASE_GATEWAY = "https://ai.cutad.web.id/v1"
PROVIDER = "cutad"
FILE_LARANG = "model_max_output_tokens"


def _bagian_provider(isi: str) -> tuple[int, int] | None:
    """Rentang baris (awal, akhir) tabel `[model_providers.cutad]`, 0-based."""
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


def perlu_shim(isi: str) -> bool:
    """True bila provider `cutad` ada tapi `base_url`-nya bukan loopback shim."""
    rentang = _bagian_provider(isi)
    if rentang is None:
        return False
    awal, akhir = rentang
    for baris in isi.splitlines()[awal:akhir]:
        kandung = baris.strip()
        if kandung.startswith("base_url"):
            nilai = kandung.split("=", 1)[1].strip().strip('"').strip("'")
            return nilai != BASE_SHIM
    return True


def arahkan_ke_shim(isi: str) -> str:
    """Kembalikan isi config dengan provider cutad -> shim, tanpa key deprecated.

    Idempoten. Hanya dua hal yang disentuh: baris `base_url` di tabel
    `[model_providers.cutad]` dan baris `model_max_output_tokens` top-level.
    Semua tabel lain (proyek, provider lain, `[windows]`) dibiarkan.
    """
    baris = isi.splitlines()
    rentang = _bagian_provider(isi)
    if rentang is not None:
        awal, akhir = rentang
        for i in range(awal, akhir):
            if baris[i].strip().startswith("base_url"):
                baris[i] = 'base_url = "%s"' % BASE_SHIM
                break
        else:
            baris.insert(awal + 1, 'base_url = "%s"' % BASE_SHIM)

    # Buang key deprecation (hanya bila assignment top-level / sebelum tabel).
    hasil = []
    untuk_tabel = True
    for b in baris:
        if b.strip().startswith("["):
            untuk_tabel = False
        if untuk_tabel and b.strip().startswith(FILE_LARANG):
            continue
        hasil.append(b)

    teks = "\n".join(hasil)
    if isi.endswith("\n") and not teks.endswith("\n"):
        teks += "\n"
    return teks


def path_config() -> str:
    """Lokasi config default: `$CODEX_HOME/config.toml` atau `~/.codex`."""
    dasar = os.environ.get("CODEX_HOME") or os.path.join(
        os.path.expanduser("~"), ".codex")
    return os.path.join(dasar, "config.toml")


def terapkan(path: str | None = None, backup_dir: str | None = None) -> dict:
    """Tulis config shim; backup berstempel waktu dibuat sebelum menulis."""
    target = path or path_config()
    with open(target, encoding="utf-8") as f:
        isi = f.read()

    if not perlu_shim(isi):
        return {"path": target, "status": "sudah-ok"}

    folder = backup_dir or os.path.dirname(target)
    stempel = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    cadangan = os.path.join(folder, "config.toml.bak-%s-shim" % stempel)
    shutil.copy2(target, cadangan)

    baru = arahkan_ke_shim(isi)
    with open(target, "w", encoding="utf-8", newline="\n") as f:
        f.write(baru)
    return {"path": target, "status": "fixed", "backup": cadangan,
            "base_url": BASE_SHIM}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Arahkan config Codex ke shim Responses lokal")
    parser.add_argument("--cek", action="store_true", help="hanya periksa")
    parser.add_argument("--path", default=None, help="config.toml alternatif")
    args = parser.parse_args(argv)

    target = args.path or path_config()
    with open(target, encoding="utf-8") as f:
        isi = f.read()

    if args.cek:
        if perlu_shim(isi):
            print("%s: base_url BELUM menunjuk shim (%s)" % (target, BASE_SHIM))
            return 1
        print("%s: sudah menunjuk shim (%s)" % (target, BASE_SHIM))
        return 0

    hasil = terapkan(target)
    if hasil["status"] == "sudah-ok":
        print("sudah-ok: %s -> %s" % (target, BASE_SHIM))
        return 0
    print("fixed: %s -> %s (backup %s)"
          % (target, BASE_SHIM, os.path.basename(hasil["backup"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())