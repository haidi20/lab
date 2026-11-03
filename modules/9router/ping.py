import requests
import os
import sys
import time
import json
from datetime import datetime

MODEL = "z-ai/glm-5.2"

CUTAD_API_KEY = os.environ["CUTAD_API_KEY"]

PERTANYAAN = "halo, bhs indo"

# Dua URL yang mau dibandingkan.
# Target pertama pakai Authorization, target kedua (9router lokal) TANPA Authorization.
TARGETS = [
    {
        "nama": "ai.cutad.web.id",
        "url": "https://ai.cutad.web.id/v1/chat/completions",
        "headers": {
            "Authorization": f"Bearer {CUTAD_API_KEY}",
            "Content-Type": "application/json",
        },
        "model": MODEL,
    },
    {
        "nama": "9router lokal",
        "url": "http://127.0.0.1:20128/v1/chat/completions",
        "headers": {
            "Content-Type": "application/json",
        },
        "model": "cd/z-ai/glm-5.2",
    },
]


def ekstrak_content(body):
    """Ambil isi jawaban dari respons chat completion; fallback ke JSON mentah."""
    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return json.dumps(body, ensure_ascii=False)


def kirim_chat(target, pertanyaan=PERTANYAAN):
    payload = {
        "model": target["model"],
        "messages": [
            {
                "role": "user",
                "content": pertanyaan,
            }
        ],
    }

    mulai = time.perf_counter()
    try:
        # Mengirim POST request
        response = requests.post(
            target["url"], headers=target["headers"], json=payload, timeout=30
        )
        durasi = time.perf_counter() - mulai
        waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Mengecek status dan mencetak respons
        if response.status_code == 200:
            try:
                body = response.json()
            except ValueError:
                # 9router kadang mengembalikan JSON utuh + artefak SSE
                # ("data: [DONE]") di ekor body dengan content-type
                # text/event-stream. Ambil objek JSON pertama dari body.
                teks = response.text
                body = json.loads(teks[: teks.rindex("}") + 1])
            content = ekstrak_content(body)
            print(f"[{waktu_sekarang}] {target['url']} Berhasil! Respons: {content}")
            return {
                "url": target["url"],
                "ok": True,
                "status_code": response.status_code,
                "content": content,
                "durasi": durasi,
            }

        print(
            f"[{waktu_sekarang}] {target['url']} Gagal! "
            f"Status: {response.status_code}, Respons: {response.text}"
        )
        return {
            "url": target["url"],
            "ok": False,
            "status_code": response.status_code,
            "error": response.text,
            "durasi": durasi,
        }

    except requests.exceptions.RequestException as e:
        durasi = time.perf_counter() - mulai
        print(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
            f"{target['url']} Terjadi kesalahan jaringan: {e}"
        )
        return {
            "url": target["url"],
            "ok": False,
            "status_code": None,
            "error": str(e),
            "durasi": durasi,
        }


def format_ringkasan(hasil_semua):
    """Susun baris ringkasan: status tiap URL + kesimpulan mana yang berhasil/gagal."""
    baris = ["", "=== Ringkasan Perbandingan ==="]
    for hasil in hasil_semua:
        tanda = "✅ BERHASIL" if hasil["ok"] else "❌ GAGAL"
        baris.append(f"{tanda} | {hasil['url']} | status={hasil['status_code']} | {hasil['durasi']:.2f}s")
        if hasil["ok"]:
            cuplikan = " ".join(str(hasil["content"]).split())
            if len(cuplikan) > 120:
                cuplikan = cuplikan[:120] + "..."
            baris.append(f"             Jawaban: {cuplikan}")
        else:
            baris.append(f"             Error  : {hasil['error']}")

    berhasil = [h["url"] for h in hasil_semua if h["ok"]]
    gagal = [h["url"] for h in hasil_semua if not h["ok"]]

    baris.append("")
    baris.append("--- Kesimpulan ---")
    baris.append("URL BERHASIL: " + ("; ".join(berhasil) if berhasil else "tidak ada"))
    baris.append("URL GAGAL   : " + ("; ".join(gagal) if gagal else "tidak ada"))
    return baris


def bandingkan(pertanyaan=PERTANYAAN):
    """Kirim pertanyaan yang sama ke semua TARGETS lalu kembalikan hasilnya."""
    hasil_semua = [kirim_chat(target, pertanyaan) for target in TARGETS]

    for baris in format_ringkasan(hasil_semua):
        print(baris)

    return hasil_semua


if __name__ == "__main__":
    if "--loop" in sys.argv:
        os.system("cls" if os.name == "nt" else "clear")
        print("Memulai perbandingan otomatis setiap 30 detik. Tekan Ctrl+C untuk menghentikan.")
        while True:
            bandingkan()
            # Jeda selama 30 detik sebelum pengulangan berikutnya
            time.sleep(30)
    else:
        print("Membandingkan dua URL chat completion...\n")
        bandingkan()
