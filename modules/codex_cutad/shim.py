"""Shim Responses->Responses untuk Codex CLI + gateway CutadAI.

Codex 0.167.1 hanya mau berbicara `wire_api = "responses"` (mode `chat` sudah
dihapus), sedangkan gateway `ai.cutad.web.id` menerima `/v1/responses` **hanya**
bila tidak memakai dua field berikut:

    role: "developer"          -> 400 request_rejected
    previous_response_id       -> 400 unsupported_parameter

Shim ini mendengar di `127.0.0.1:8787`, menulis ulang dua hal itu, lalu
meneruskan request (termasuk stream SSE) apa adanya ke gateway. Tidak ada
terjemahan Responses->Chat; field lain (`tools`, `reasoning`, `instructions`,
`prompt_cache_key`, `parallel_tool_calls`, `include`, `max_output_tokens`)
terbukti diterima gateway 200 dan dibiarkan utuh.

Jalankan: `python -m modules.codex_cutad.shim [--port 8787]`
Lalu set `~/.codex/config.toml`:

    [model_providers.cutad]
    base_url = "http://127.0.0.1:8787/v1"
    wire_api = "responses"
    env_key  = "CODEX_CUTAD_API_KEY"

Token tidak pernah ditulis ke log; shim memakai `CODEX_CUTAD_API_KEY` (fallback
`CUTAD_API_KEY`) dari environment, bukan dari header klien.
"""
from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE_DEFAULT = "https://ai.cutad.web.id/v1"
PORT_DEFAULT = 8787
HOST_DEFAULT = "127.0.0.1"

# Header hop-by-hop / milik koneksi klien yang tidak boleh diteruskan.
HEADER_DIBUANG = {
    "host", "content-length", "connection", "keep-alive", "transfer-encoding",
    "upgrade", "proxy-authorization", "proxy-authenticate", "te", "trailer",
    "authorization",
}


def url_target(path: str, base: str = BASE_DEFAULT) -> str:
    """URL upstream; menerima `/v1/responses` maupun `/responses`."""
    bersih = path.split("?", 1)[0]
    if bersih.startswith("/v1/"):
        bersih = bersih[len("/v1"):]
    elif not bersih.startswith("/"):
        bersih = "/" + bersih
    return base.rstrip("/") + bersih


def token_dari_env() -> str | None:
    """Token gateway dari environment; `CODEX_CUTAD_API_KEY` diutamakan."""
    for nama in ("CODEX_CUTAD_API_KEY", "CUTAD_API_KEY"):
        nilai = (os.environ.get(nama) or "").strip()
        if nilai:
            return nilai
    return None


def header_ke_upstream(headers, token: str | None) -> dict:
    """Header untuk upstream: buang hop-by-hop + auth klien, pasang auth server."""
    hasil = {}
    for nama, nilai in headers.items():
        if nama.lower() in HEADER_DIBUANG:
            continue
        hasil[nama.title()] = nilai
    hasil.setdefault("Content-Type", "application/json")
    if token:
        hasil["Authorization"] = "Bearer " + token
    return hasil


def ganti_developer(payload: dict) -> tuple[dict, int]:
    """Salin payload, ubah semua `role: developer` pada `input` jadi `system`.

    Mengembalikan (payload_baru, jumlah_yang_diubah). Non-destruktif: objek
    asli tidak pernah dimutasi, dan `input` berbentuk string dibiarkan apa
    adanya karena gateway menerimanya.
    """
    baru = dict(payload)
    item = baru.get("input")
    if not isinstance(item, list):
        return baru, 0

    hasil = []
    diubah = 0
    for entri in item:
        if isinstance(entri, dict) and entri.get("role") == "developer":
            entri = {**entri, "role": "system"}
            diubah += 1
        hasil.append(entri)
    if diubah:
        baru["input"] = hasil
    return baru, diubah


def ratakan_namespace_tools(payload: dict) -> tuple[dict, int]:
    """Ubah tool `type: "namespace"` menjadi function-function terpisah.

    Gateway menolak `type: "namespace"` (HTTP 400) namun menerima semua
    sub-tool di dalamnya bila dikirim sebagai function biasa. Sub-tool sudah
    berbentuk function lengkap, jadi cukup diangkat ke level `tools`.

    Catatan: setelah diratakan, pemanggilan `namespace.tool` tidak lagi
    dikenali gateway; ini konsekuensi yang diterima agar sesi Codex tetap
    bisa berjalan. Mengembalikan (payload_baru, jumlah_namespace_yang_diratakan).
    """
    baru = dict(payload)
    tools = baru.get("tools")
    if not isinstance(tools, list):
        return baru, 0

    hasil = []
    diratakan = 0
    for tool in tools:
        if (
            isinstance(tool, dict)
            and tool.get("type") == "namespace"
            and isinstance(tool.get("tools"), list)
        ):
            hasil.extend(tool["tools"])
            diratakan += 1
        else:
            hasil.append(tool)
    if diratakan:
        baru["tools"] = hasil
    return baru, diratakan


def ringkas_reasoning(payload: dict) -> tuple[dict, int]:
    """Buang `reasoning.summary` (ditolak gateway 400/3051), sisakan effort.

    Gateway CutadAI menerima `reasoning: {effort: ...}` tetapi menolak
    `reasoning.summary` (diverifikasi 2026-11-24 lewat
    `modules.codex_cutad.diagnosa_3051`). Codex 0.167.1 selalu mengirim
    keduanya, jadi summary harus dibuang agar request tidak 400.
    `reasoning` yang tinggal kosong ikut dihapus.
    """
    baru = dict(payload)
    reasoning = baru.get("reasoning")
    if not isinstance(reasoning, dict) or "summary" not in reasoning:
        return baru, 0
    sisa = {k: v for k, v in reasoning.items() if k != "summary"}
    if sisa:
        baru["reasoning"] = sisa
    else:
        baru.pop("reasoning")
    return baru, 1


def buang_tool_tak_didukung(payload: dict) -> tuple[dict, int]:
    """Buang tool `type: "web_search"` yang ditolak gateway (400/3051).

    Codex 0.167.1 selalu menyertakan tool `web_search` bawaan. Gateway CutadAI
    menolaknya sebagai "Invalid request parameters" (diverifikasi 2026-11-24
    lewat `modules.codex_cutad.diagnosa_3051`), jadi tool itu dibuang supaya
    sesi Codex tetap bisa berjalan tanpa pencarian web sisi server.
    """
    baru = dict(payload)
    tools = baru.get("tools")
    if not isinstance(tools, list):
        return baru, 0
    sisa = [t for t in tools
            if not (isinstance(t, dict) and t.get("type") == "web_search")]
    dibuang = len(tools) - len(sisa)
    if dibuang:
        baru["tools"] = sisa
    return baru, dibuang


def bersihkan_payload(payload: dict) -> tuple[dict, dict]:
    """Rewrite minimal yang membuat gateway menerima payload Codex.

    Lima perubahan: `developer -> system`, buang `previous_response_id`,
    ratakan tool namespace menjadi function, buang `reasoning.summary`, dan
    buang tool `web_search`. Gateway tidak mendukung chaining respons, jadi
    Codex harus mengirim riwayat penuh -- itu perilaku default Codex bila shim
    tidak mengembalikan id lama. Mengembalikan (payload_baru, info).
    """
    baru, diubah = ganti_developer(payload)
    baru, diratakan = ratakan_namespace_tools(baru)
    baru, ada_summary = ringkas_reasoning(baru)
    baru, web_search = buang_tool_tak_didukung(baru)
    buang = "previous_response_id" in baru
    if buang:
        baru = {k: v for k, v in baru.items() if k != "previous_response_id"}
    return baru, {
        "developer": diubah,
        "buang_prev": buang,
        "namespace": diratakan,
        "reasoning_summary": ada_summary,
        "web_search": web_search,
    }


def ringkas_log(path: str, payload: dict, info: dict) -> str:
    """Satu baris log tanpa kredensial (tidak ada token / header auth)."""
    status = info.get("status")
    bagian = ["%s model=%s" % (path, payload.get("model", "-"))]
    if info.get("developer"):
        bagian.append("developer->system=%d" % info["developer"])
    if info.get("buang_prev"):
        bagian.append("previous_response_id=dibuang")
    if info.get("namespace"):
        bagian.append("namespace_ditrogenkan=%d" % info["namespace"])
    if info.get("reasoning_summary"):
        bagian.append("reasoning.summary=dibuang")
    if info.get("web_search"):
        bagian.append("web_search_dibuang=%d" % info["web_search"])
    if status is not None:
        bagian.append("status=%s" % status)
    return " | ".join(bagian)


def ratakan_teks(nilai) -> str:
    """Normalkan nilai teks Responses API menjadi string yang bisa dibaca.

    Spesifikasi Responses API mewajibkan `delta`, `text`, dan
    `output_text.text` bertipe string. 9router@0.5.119 kadang mengirim array
    objek reasoning di posisi itu; Codex lalu memanggil `String(nilai)` dan
    hasilnya `[object Object]`. Fungsi ini mengekstrak isi teksnya agar tidak
    pernah ada `[object Object]` yang sampai ke pengguna.

    Bentuk yang dikenali: string (apa adanya), None (""), list (digabung),
    dict (`text` / `thinking` / `content`), dan skalar lain (str()).
    """
    if nilai is None:
        return ""
    if isinstance(nilai, str):
        return nilai
    if isinstance(nilai, bool):
        return "true" if nilai else "false"
    if isinstance(nilai, (int, float)):
        return str(nilai)
    if isinstance(nilai, list):
        return "".join(ratakan_teks(item) for item in nilai)
    if isinstance(nilai, dict):
        for kunci in ("text", "thinking", "content", "delta"):
            if kunci in nilai:
                return ratakan_teks(nilai[kunci])
        return ""
    return str(nilai)


_EVENT_DELTA_TEKS = "response.output_text.delta"
_EVENT_DELTA_REASONING = "response.reasoning_summary_text.delta"


def _ada_chunk_reasoning(delta) -> bool:
    """True bila `delta` memuat objek reasoning/thinking (bukan teks jawaban)."""
    if not isinstance(delta, list):
        return False
    for entri in delta:
        if not isinstance(entri, dict):
            continue
        if entri.get("type") in ("thinking", "reasoning"):
            return True
        if "thinking" in entri or "reasoning" in entri:
            return True
    return False


def _blok_sse(nama_event: str, payload: dict) -> bytes:
    """Serialisasi satu event SSE kembali menjadi blok `event:`/`data:`."""
    badan = json.dumps(payload, ensure_ascii=False).encode()
    return b"event: " + nama_event.encode() + b"\ndata: " + badan + b"\n\n"


def normalisasi_baris_sse(blok: bytes) -> tuple[list[bytes], dict]:
    """Perbaiki satu blok SSE Responses yang melanggar tipe wajib.

    Mengembalikan (daftar_blok_baru, info). Blok yang sudah benar dikembalikan
    apa adanya (byte identik). Dua kasus yang ditangani:

    1. `response.output_text.delta` dengan `delta` non-string. Bila isinya
       chunk reasoning, event diganti menjadi
       `response.reasoning_summary_text.delta` supaya reasoning tidak
       mengotori teks jawaban. Selain itu `delta` dijadikan string.
    2. `output_text.done` / `content_part.done` / `output_item.done` dengan
       field teks non-string -> dinormalkan menjadi string.

    Blok yang bukan event data (komentar `:`, keep-alive, JSON rusak)
    diteruskan tanpa perubahan agar stream tidak pernah pecah.
    """
    info = {"dipindah": 0, "dinormalkan": 0}
    teks = blok.decode("utf-8", "replace")
    baris = [b for b in teks.splitlines() if b.startswith("data:")]
    if not baris:
        return [blok], info

    badan = baris[0][len("data:"):].strip()
    try:
        payload = json.loads(badan)
    except (json.JSONDecodeError, ValueError):
        return [blok], info
    if not isinstance(payload, dict):
        return [blok], info

    nama = payload.get("type") or "message"
    asli_event = nama
    for b in teks.splitlines():
        if b.startswith("event:"):
            asli_event = b[len("event:"):].strip()
            break

    if nama == "response.output_text.done" and not isinstance(
            payload.get("text"), str):
        payload["text"] = ratakan_teks(payload.get("text"))
        info["dinormalkan"] += 1

    elif nama == "response.content_part.done":
        bagian = payload.get("part")
        if isinstance(bagian, dict) and not isinstance(bagian.get("text"), str):
            bagian["text"] = ratakan_teks(bagian.get("text"))
            info["dinormalkan"] += 1

    elif nama == "response.output_item.done":
        item = payload.get("item")
        if isinstance(item, dict) and isinstance(item.get("content"), list):
            for bagian in item["content"]:
                if isinstance(bagian, dict) and not isinstance(
                        bagian.get("text"), str):
                    bagian["text"] = ratakan_teks(bagian.get("text"))
                    info["dinormalkan"] += 1

    elif nama == _EVENT_DELTA_TEKS:
        delta = payload.get("delta")
        if isinstance(delta, str):
            return [blok], info
        if _ada_chunk_reasoning(delta):
            payload["type"] = _EVENT_DELTA_REASONING
            payload["delta"] = ratakan_teks(delta)
            payload["summary_index"] = payload.get("summary_index", 0)
            info["dipindah"] += 1
            return [_blok_sse(_EVENT_DELTA_REASONING, payload)], info
        rata = ratakan_teks(delta)
        if not rata:
            info["dipindah"] += 1
            return [], info
        payload["delta"] = rata
        info["dinormalkan"] += 1

    if payload.get("type") == asli_event and info["dinormalkan"] == 0:
        return [blok], info
    return [_blok_sse(asli_event, payload)], info


def _konteks_ssl():
    """Konteks TLS; pakai certifi bila ada (umum di Windows)."""
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:  # noqa: BLE001 - certifi opsional
        return ssl.create_default_context()


class Handler(BaseHTTPRequestHandler):
    """Proxy transparan dengan rewrite dua field."""

    protocol_version = "HTTP/1.1"
    server_version = "codex-cutad-shim/1.0"

    # diisi oleh buat_server
    base_url = BASE_DEFAULT
    token = None

    def log_message(self, format, *args):  # noqa: A002,ANN001
        """Bungkam log default (berisi path klien); pakai ringkas_log."""
        return

    def _kirim_error(self, kode: int, pesan: str) -> None:
        badan = json.dumps({"error": {"message": pesan}}).encode()
        self.send_response(kode)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(badan)))
        self.end_headers()
        self.wfile.write(badan)

    def do_GET(self):  # noqa: N802
        self._teruskan(badan=None)

    def do_POST(self):  # noqa: N802
        panjang = int(self.headers.get("Content-Length") or 0)
        mentah = self.rfile.read(panjang) if panjang else b""
        try:
            payload = json.loads(mentah) if mentah else {}
        except json.JSONDecodeError:
            self._kirim_error(400, "body bukan JSON valid")
            return

        baru, info = bersihkan_payload(payload)
        hasil = self._teruskan(badan=json.dumps(baru).encode())
        print(ringkas_log(self.path, baru, {**info, "status": hasil}),
              file=sys.stderr, flush=True)

    def _teruskan(self, badan):
        """Kirim ke upstream dan salin balasan (termasuk SSE) ke klien."""
        url = url_target(self.path, self.base_url)
        header = header_ke_upstream(self.headers, self.token)
        req = urllib.request.Request(
            url, data=badan, method=self.command, headers=header)

        try:
            upstream = urllib.request.urlopen(
                req, timeout=600, context=_konteks_ssl())
        except urllib.error.HTTPError as exc:
            isi = exc.read()
            self.send_response(exc.code)
            self.send_header("Content-Type", exc.headers.get(
                "Content-Type", "application/json"))
            self.send_header("Content-Length", str(len(isi)))
            self.end_headers()
            self.wfile.write(isi)
            return exc.code
        except Exception as exc:  # noqa: BLE001 - jaringan/SSL
            self._kirim_error(502, "gagal menghubungi gateway: %s"
                              % type(exc).__name__)
            return 502

        with upstream:
            status = upstream.status
            tipe = upstream.headers.get("Content-Type", "application/json")
            if "text/event-stream" in tipe:
                # Stream SSE: salin per baris agar Codex melihat token segera.
                self.send_response(status)
                self.send_header("Content-Type", tipe)
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "close")
                self.close_connection = True
                self.end_headers()
                for baris in upstream:
                    for keluaran in normalisasi_baris_sse(baris)[0]:
                        try:
                            self.wfile.write(keluaran)
                            self.wfile.flush()
                        except (BrokenPipeError, ConnectionResetError):
                            return status
                return status

            isi = upstream.read()
            self.send_response(status)
            self.send_header("Content-Type", tipe)
            self.send_header("Content-Length", str(len(isi)))
            self.end_headers()
            self.wfile.write(isi)
            return status


def buat_server(port: int = PORT_DEFAULT, base: str = BASE_DEFAULT,
                token: str | None = None,
                host: str = HOST_DEFAULT) -> ThreadingHTTPServer:
    """Buat (tanpa menjalankan) server shim. Port 0 = port acak (untuk test)."""
    kelas = type("ShimHandler", (Handler,), {
        "base_url": base,
        "token": token if token is not None else token_dari_env(),
    })
    server = ThreadingHTTPServer((host, port), kelas)
    server.daemon_threads = True
    return server


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Shim Responses Codex -> gateway CutadAI")
    parser.add_argument("--port", type=int, default=PORT_DEFAULT)
    parser.add_argument("--host", default=HOST_DEFAULT)
    parser.add_argument("--base", default=os.environ.get(
        "CODEX_CUTAD_BASE_URL", BASE_DEFAULT))
    args = parser.parse_args(argv)

    if not token_dari_env():
        print("PERINGATAN: CODEX_CUTAD_API_KEY kosong; request akan 401.",
              file=sys.stderr)

    server = buat_server(port=args.port, base=args.base, host=args.host)
    print("shim jalan di http://%s:%d/v1 -> %s"
          % (args.host, server.server_address[1], args.base),
          file=sys.stderr, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("shim dihentikan", file=sys.stderr)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

