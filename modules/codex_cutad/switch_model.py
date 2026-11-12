"""Ganti model DEFAULT Codex CLI / panel Cursor di balik shim CutadAI.

Latar (diverifikasi 2026-11-11/12, Codex CLI 0.167.1, Windows):
- `~/.codex/config.toml` default: `model = "tencent/hy4-preview"` +
  `model_provider = "cutad"` (shim `hy4_proxy.py` di 127.0.0.1:8787).
- Gateway CutadAI membalas 400 kode 11128
  ("Upstream error. Contact support if this persists.") untuk payload yang
  tidak didukung: `role:"developer"` (Hy4 preview) dan `previous_response_id`
  (kira-kira semua model, dikirim Codex sejak turn kedua). Codex 0.167.1
  responses-only selalu mengirim keduanya, jadi SEMUA model non-OpenAI di
  gateway ini wajib lewat shim.
- `deepseek-v4-pro` (probe 2026-11-12): 200 untuk payload developer,
  reasoning, dan payload Codex penuh -> cukup lewat shim, tanpa ganti apa pun
  selain nama model.

Aturan anti "Upstream error": nama model TIDAK PERNAH ditulis sebelum probe
`/v1/responses` mengembalikan 200 untuk model tersebut
(`modules/codex_cutad/probe_model.py`).

Tabel `[model_providers.cutad-direct]` dipertahankan sebagai fallback, dan
profil `glm.config.toml` tetap ada untuk `codex --profile glm`.

`model_max_output_tokens` sengaja TIDAK ditambahkan: Codex 0.167.1
mengabaikannya dengan warning "unrecognized configuration setting".

Pakai:
    python -m modules.codex_cutad.switch_model --cek             # inspeksi
    python -m modules.codex_cutad.switch_model                   # default Hy4
    python -m modules.codex_cutad.switch_model deepseek-v4-pro   # model lain
Config default: ~/.codex/config.toml (override: env CODEX_CONFIG).
"""
from __future__ import annotations

import os
import sys
import time

from modules.codex_cutad import probe_model as probe

MODEL_HY4 = "tencent/hy4-preview"
MODEL_DEFAULT = MODEL_HY4
PROVIDER_HY4 = "cutad"
SHIM_BASE_URL = "http://127.0.0.1:8787/v1"

ALASAN = (
    "Codex 0.167.1 (responses-only) selalu mengirim role:\"developer\" dan "
    "previous_response_id; gateway CutadAI membalas 400 kode 11128 "
    "\"Upstream error\" untuk keduanya -> wajib lewat [model_providers.cutad] "
    "(hy4_proxy.py di 127.0.0.1:8787)."
)


def path_config_default():
    """Path config default, bisa dioverride lewat env CODEX_CONFIG."""
    return os.environ.get("CODEX_CONFIG") or os.path.expanduser(
        "~/.codex/config.toml"
    )


def _nilai_top_level(isi, kunci):
    """Ambil nilai key top-level TOML (sebelum header [tabel] pertama).

    Kunci global Codex wajib berada sebelum `[...]` pertama; setelahnya semua
    assignment milik tabel, jadi jangan ikut terbaca (mis. `model` di dalam
    `[model_providers...]` bila ada).
    """
    for baris in isi.splitlines():
        kandung = baris.strip()
        if kandung.startswith("["):
            return None
        if not kandung or kandung.startswith("#"):
            continue
        if "=" not in kandung:
            continue
        nama, nilai = kandung.split("=", 1)
        if nama.strip() == kunci:
            return nilai.strip().strip('"').strip("'") or None
    return None


def model_dari_config(isi):
    """Nilai `model` top-level, atau None bila tidak ada."""
    return _nilai_top_level(isi, "model")


def provider_dari_config(isi):
    """Nilai `model_provider` top-level, atau None bila tidak ada."""
    return _nilai_top_level(isi, "model_provider")


def sudah_hy4(isi):
    """True bila model DAN provider default sudah menunjuk Hy4 via shim."""
    return sudah_benar(isi, MODEL_HY4)


def sudah_benar(isi, model=None):
    """True bila `model` (default Hy4) sudah dipakai via provider shim."""
    target = model or MODEL_DEFAULT
    return (
        model_dari_config(isi) == target
        and provider_dari_config(isi) == PROVIDER_HY4
    )


def _ganti_baris(isi, kunci, nilai_baru):
    """Ganti nilai assignment top-level `kunci`, sisipkan bila belum ada.

    Hanya menyentuh baris top-level (sebelum header tabel pertama) sehingga
    tabel `[model_providers.*]` tidak pernah terubah. Mengembalikan list baris.
    """
    baris_baru = f'{kunci} = "{nilai_baru}"'
    baris_list = isi.splitlines()
    batas_tabel = len(baris_list)
    for i, baris in enumerate(baris_list):
        if baris.strip().startswith("["):
            batas_tabel = i
            break

    ditemukan = False
    for i in range(batas_tabel):
        kandung = baris_list[i].strip()
        if kandung.startswith("#") or "=" not in kandung:
            continue
        if kandung.split("=", 1)[0].strip() == kunci:
            baris_list[i] = baris_baru
            ditemukan = True
            break

    if not ditemukan:
        # Sisipkan di dekat key top-level sejenis, sebelum tabel pertama.
        sisi = batas_tabel
        for j in range(batas_tabel):
            if baris_list[j].strip().startswith("model"):
                sisi = j + 1
                break
        baris_list.insert(sisi, baris_baru)
    return baris_list


def ubah_ke_hy4(isi):
    """Kembalikan isi config dengan default model = Hy4 preview via shim.

    Idempoten: memanggil dua kali menghasilkan string identik. Komentar,
    metadata model, tabel proyek, dan tabel provider lain dipertahankan apa
    adanya; `model_max_output_tokens` tidak pernah ditambahkan.
    """
    return ubah_model(isi, MODEL_HY4)


def ubah_model(isi, model):
    """Ganti default `model` ke `model` dan provider ke shim `cutad`.

    Idempoten untuk target apa pun. Hanya key top-level yang disentuh; fungsi
    ini TIDAK memvalidasi model ke gateway (itu tugas `terapkan` lewat probe).
    """
    target = model or MODEL_DEFAULT
    if sudah_benar(isi, target):
        return isi
    baris = _ganti_baris(isi, "model", target)
    baris = _ganti_baris("\n".join(baris), "model_provider", PROVIDER_HY4)
    teks = "\n".join(baris)
    if isi.endswith("\n"):
        teks += "\n"
    return teks


def terapkan(path_config, backup_dir=None, target=None):
    """Terapkan switch ke file; kembalikan status terstruktur.

    Sebelum menulis apa pun, model target di-probe ke `/v1/responses`. Bila
    probe gagal (mis. 400 kode 11128 "Upstream error"), file TIDAK disentuh
    sama sekali dan status 'probe-gagal' dikembalikan -- supaya Codex tidak
    pernah diarahkan ke model yang membuat sesi berhenti dengan upstream error.

    Backup berstempel waktu dibuat sebelum menulis. Tidak mengubah file bila
    config sudah benar (status 'sudah-ok').
    """
    model = target or MODEL_DEFAULT
    with open(path_config, encoding="utf-8") as f:
        isi = f.read()

    dari = model_dari_config(isi)
    provider_dari = provider_dari_config(isi)
    if sudah_benar(isi, model):
        return {
            "path": path_config,
            "status": "sudah-ok",
            "dari": dari,
            "ke": model,
            "provider": provider_dari,
        }

    token = probe.token_dari_config(isi)
    url = probe.base_url_dari_config(isi)
    hasil_probe = probe.kirim(probe.varian(model)["minimal"], token, url)
    if not hasil_probe.get("ok"):
        return {
            "path": path_config,
            "status": "probe-gagal",
            "dari": dari,
            "ke": model,
            "status_http": hasil_probe.get("status"),
            "kode": hasil_probe.get("kode"),
            "pesan": hasil_probe.get("teks"),
        }

    if backup_dir is None:
        backup_dir = os.path.dirname(path_config) or "."
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup_path = os.path.join(
        backup_dir, f"{os.path.basename(path_config)}.bak-{stamp}"
    )
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(isi)

    with open(path_config, "w", encoding="utf-8") as f:
        f.write(ubah_model(isi, model))

    return {
        "path": path_config,
        "status": "fixed",
        "dari": dari,
        "ke": model,
        "provider_dari": provider_dari,
        "provider_ke": PROVIDER_HY4,
        "backup": backup_path,
        "probe": hasil_probe.get("teks"),
    }




def main():
    argumen = sys.argv[1:]
    path = path_config_default()
    target = None
    for arg in argumen:
        if not arg.startswith("-"):
            target = arg
    target = target or MODEL_DEFAULT

    if not os.path.exists(path):
        print(f"Config tidak ditemukan: {path}")
        return 1

    with open(path, encoding="utf-8") as f:
        isi = f.read()

    if "--cek" in argumen:
        print(f"config        : {path}")
        print(f"model         : {model_dari_config(isi)}")
        print(f"model_provider: {provider_dari_config(isi)}")
        print(f"target        : {target}")
        print(f"sudah benar   : {sudah_benar(isi, target)}")
        return 0

    hasil = terapkan(path, target=target)
    if hasil["status"] == "sudah-ok":
        print(f"OK  {path} sudah memakai {target} via {PROVIDER_HY4}")
        return 0

    if hasil["status"] == "probe-gagal":
        print(f"BATAL  {path} TIDAK diubah (model tetap '{hasil['dari']}')")
        print(f"    target probe : {hasil['ke']}")
        print(f"    hasil probe  : HTTP {hasil['status_http']} "
              f"kode={hasil['kode']} {hasil['pesan']}")
        print("    Probe gagal -> switch dibatalkan supaya Codex tidak "
              "berakhir 'Upstream error. Contact support if this persists.'")
        print("    Cek dulu: python -m modules.codex_cutad.probe_model "
              f"{hasil['ke']} --semua-varian")
        return 3

    print(f"FIX {path}: model '{hasil['dari']}' -> '{hasil['ke']}'")
    print(f"    provider '{hasil['provider_dari']}' -> '{hasil['provider_ke']}'")
    print(f"    probe: {hasil['probe']}")
    print(f"    backup: {hasil['backup']}")
    print(f"    alasan: {ALASAN}")
    print("    Pastikan hy4_proxy.py jalan di 127.0.0.1:8787, lalu restart Codex.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
