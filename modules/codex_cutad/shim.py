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


def bersihkan_payload(payload: dict) -> tuple[dict, dict]:
    """Rewrite minimal yang membuat gateway menerima payload Codex.

    Tiga perubahan: `developer -> system`, buang `previous_response_id`, dan
    ratakan tool namespace menjadi function. Gateway tidak mendukung chaining
    respons, jadi Codex harus mengirim riwayat penuh -- itu perilaku default
    Codex bila shim tidak mengembalikan id lama.
    Mengembalikan (payload_baru, info).
    """
    baru, diubah = ganti_developer(payload)
    baru, diratakan = ratakan_namespace_tools(baru)
    buang = "previous_response_id" in baru
    if buang:
        baru = {k: v for k, v in baru.items() if k != "previous_response_id"}
    return baru, {
        "developer": diubah,
        "buang_prev": buang,
        "namespace": diratakan,
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
    if status is not None:
        bagian.append("status=%s" % status)
    return " | ".join(bagian)


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
                    try:
                        self.wfile.write(baris)
                        self.wfile.flush()
                    except (BrokenPipeError, ConnectionResetError):
                        break
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

