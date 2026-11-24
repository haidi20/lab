"""Cari field payload Codex yang membuat gateway membalas 400/3051.

Jalankan: python -m modules.codex_cutad.diagnosa_3051
Token diambil dari 9router (provider `cd`), tidak pernah dicetak.
"""
import argparse
import json
import os
import random
import time
import sqlite3
import ssl
import urllib.error
import urllib.request

URL = "https://ai.cutad.web.id/v1/responses"
DB = os.path.join(os.environ.get("APPDATA", ""), "9router", "db", "data.sqlite")


def token() -> str:
    koneksi = sqlite3.connect(DB)
    try:
        baris = koneksi.execute(
            "select json_extract(data,'$.apiKey') from providerConnections "
            "where name='cd'").fetchone()
    finally:
        koneksi.close()
    return baris[0]


def konteks():
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:  # noqa: BLE001
        return ssl._create_unverified_context()


DASAR = {
    "model": "deepseek-v4-pro",
    "input": [{"role": "user", "content": [
        {"type": "input_text", "text": "Reply exactly: OK"}]}],
    "stream": True,
}

# Kandidat field/varian yang dikirim Codex 0.167.1.
VARIAN = {
    "dasar": {},
    "client_metadata": {"client_metadata": {"origin": "codex"}},
    "web_search_tool": {"tools": [{"type": "web_search"}]},
    "tool_choice_auto": {"tool_choice": "auto"},
    "reasoning_effort_none": {"reasoning": {"effort": "none"}},
    "reasoning_effort_medium": {"reasoning": {"effort": "medium"}},
    "reasoning_effort_high": {"reasoning": {"effort": "high"}},
    "reasoning_summary_only": {"reasoning": {"summary": "auto"}},
    "include_encrypted": {"include": ["reasoning.encrypted_content"]},
    "store_false": {"store": False},
    "store_true": {"store": True},
    "parallel_tool_calls": {"parallel_tool_calls": True},
    "prompt_cache_key": {"prompt_cache_key": "abc"},
    "function_tool": {"tools": [{"type": "function", "name": "f",
                                 "description": "d",
                                 "parameters": {"type": "object",
                                                "properties": {}}}]},
}


def kirim(payload: dict, kunci: str):
    req = urllib.request.Request(
        URL, data=json.dumps(payload).encode(), method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + kunci})
    try:
        with urllib.request.urlopen(req, timeout=90, context=konteks()) as r:
            return r.status, r.read(120).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read(200).decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        return 0, type(e).__name__


def pilih_varian(varian: dict, hanya: str | None) -> dict:
    """Saring varian berdasarkan nama dipisah koma; `None` berarti semua."""
    if hanya is None:
        return dict(varian)
    nama = [n.strip() for n in hanya.split(",") if n.strip()]
    if not nama:
        return {}
    tak_dikenal = [n for n in nama if n not in varian]
    if tak_dikenal:
        raise ValueError("varian tidak dikenal: " + ", ".join(tak_dikenal))
    return {n: varian[n] for n in nama}


def jeda_acak(detik: float) -> None:
    """Tidur dengan jitter 0.8x-1.2x agar tidak menembak beruntun dan kena 429."""
    if detik <= 0:
        return
    time.sleep(detik * (0.8 + 0.4 * random.random()))


def main(argv: list | None = None) -> int:
    """Kirim tiap varian satu per satu, berjeda, lalu laporkan yang gagal."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hanya", help="nama varian dipisah koma (mis. store_false)")
    parser.add_argument("--jeda", type=float, default=6.0,
                        help="jeda dasar antar request dalam detik (default 6)")
    args = parser.parse_args(argv)

    try:
        varian = pilih_varian(VARIAN, args.hanya)
    except ValueError as exc:
        print(exc)
        return 2
    if not varian:
        print("tidak ada varian yang dipilih")
        return 2

    kunci = token()
    buruk = []
    for urutan, (nama, tambahan) in enumerate(varian.items()):
        if urutan:
            jeda_acak(args.jeda)
        kode, isi = kirim({**DASAR, **tambahan}, kunci)
        tanda = "OK " if kode == 200 else "GAGAL"
        print("%-5s %-20s %s %s" % (tanda, nama, kode, isi[:90].replace("\n", " ")))
        if kode != 200:
            buruk.append(nama)
    print("\nfield bermasalah:", ", ".join(buruk) if buruk else "(tidak ada)")
    return 0 if not buruk else 1


if __name__ == "__main__":
    raise SystemExit(main())
