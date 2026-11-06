"""Perbaiki config Codex CLI agar tidak lagi kena upstream_error cutad.

Akar masalah (diverifikasi live 2026-11-06):
- `~/.codex/config.toml` memakai `wire_api = "responses"` untuk provider
  `cutad` (https://ai.cutad.web.id/v1).
- Endpoint `/v1/responses` proxy cutad MENOLAK `stream: true`:
  400 `unsupported_parameter` untuk semua model (glm-5.2, glm-5.3-flash,
  deepseek-v4-pro). Codex CLI selalu streaming -> selalu gagal, tampil
  sebagai "upstream_error".
- Endpoint `/v1/chat/completions` terbukti 200 OK streaming + tools +
  reasoning_effort untuk ketiga model.

Fix: `wire_api = "chat"` di config Codex.

Pakai:
    python3 -m modules.codex_cutad.fix_wire_api           # perbaiki config
    python3 -m modules.codex_cutad.fix_wire_api --cek     # hanya cek
Config: default ~/.codex/config.toml, bisa dioverride env CODEX_CONFIG.
"""
import os
import sys
import time

Kata_KUNCI = "wire_api"
NILAI_BARU = "chat"

UPSTREAM_BUKTI = (
    "/v1/responses + stream:true = 400 unsupported_parameter (semua model); "
    "/v1/chat/completions + stream:true = 200 OK. Codex selalu streaming, "
    "jadi wire_api harus 'chat'."
)


def path_config_default():
    return os.environ.get("CODEX_CONFIG") or os.path.expanduser(
        "~/.codex/config.toml"
    )


def wire_api_dari_config(isi):
    """Ambil nilai wire_api dari isi config (None bila tidak ada)."""
    for baris in isi.splitlines():
        kandung = baris.strip()
        if kandung.startswith("wire_api") and "=" in kandung:
            nilai = kandung.split("=", 1)[1].strip().strip('"').strip("'")
            return nilai or None
    return None


def perlu_perbaikan(isi):
    """True bila config memakai wire_api responses (bakal kena upstream error)."""
    return wire_api_dari_config(isi) == "responses"


def ubah_wire_api(isi):
    """Ubah/ganti wire_api menjadi "chat"; kembalikan isi config baru."""
    baris_baru = f'wire_api = "{NILAI_BARU}"'
    baris_ada = None
    hasil = []
    for baris in isi.splitlines():
        if baris.strip().startswith("wire_api"):
            baris_ada = True
            hasil.append(baris_baru)
        else:
            hasil.append(baris)

    if baris_ada is None:
        # Sisipkan setelah baris model_provider teratas, atau paling atas.
        sisi = 0
        for indeks, baris in enumerate(hasil):
            if baris.strip().startswith("model_provider"):
                sisi = indeks + 1
                break
        hasil.insert(sisi, baris_baru)

    teks = "\n".join(hasil)
    if isi.endswith("\n"):
        teks += "\n"
    return teks


def terapkan(path_config, backup_dir=None):
    """Perbaiki file config; kembalikan status terstruktur tanpa merusak file."""
    with open(path_config, encoding="utf-8") as f:
        isi = f.read()

    if not perlu_perbaikan(isi):
        return {
            "path": path_config,
            "status": "sudah-ok",
            "dari": wire_api_dari_config(isi),
            "ke": NILAI_BARU,
        }

    backup_path = None
    if backup_dir is None:
        backup_dir = os.path.dirname(path_config) or "."
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup_path = os.path.join(
        backup_dir, f"{os.path.basename(path_config)}.bak-{stamp}"
    )
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(isi)

    with open(path_config, "w", encoding="utf-8") as f:
        f.write(ubah_wire_api(isi))

    return {
        "path": path_config,
        "status": "fixed",
        "dari": "responses",
        "ke": NILAI_BARU,
        "backup": backup_path,
    }


def main():
    argumen = sys.argv[1:]
    path = path_config_default()

    if not os.path.exists(path):
        print(f"Config tidak ditemukan: {path}")
        return 1

    with open(path, encoding="utf-8") as f:
        isi = f.read()

    dari = wire_api_dari_config(isi)
    if "--cek" in argumen:
        print(f"config : {path}")
        print(f"wire_api: {dari}")
        print(f"perlu perbaikan: {perlu_perbaikan(isi)}")
        return 0

    hasil = terapkan(path)
    if hasil["status"] == "sudah-ok":
        print(f"OK  {path} sudah wire_api = '{dari}' (tidak diubah)")
        return 0

    print(f"FIX {path}: wire_api '{hasil['dari']}' -> '{hasil['ke']}'")
    print(f"    backup: {hasil['backup']}")
    print(f"    alasan: {UPSTREAM_BUKTI}")
    print("    Restart Codex CLI/extension agar config baru terbaca.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
