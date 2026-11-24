"""Verifikasi manual: stream cacat 9router dinormalkan shim (tanpa jaringan).

Jalankan: python -m modules.codex_cutad.verifikasi_object_object
"""
import importlib
import json
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

shim = importlib.import_module("modules.codex_cutad.shim")

# Persis byte yang dikirim 9router@0.5.119 untuk satu turn (2026-11-24).
STREAM_9ROUTER = (
    b'event: response.created\ndata: {"type":"response.created",'
    b'"response":{"id":"resp_1","status":"in_progress","output":[]}}\n\n'
    b'event: response.output_text.delta\ndata: {"type":"response.output_text.delta",'
    b'"delta":[]}\n\n'
    b'event: response.output_text.delta\ndata: {"type":"response.output_text.delta",'
    b'"delta":[{"type":"thinking","thinking":[{"type":"text","text":"The user"}],'
    b'"closed":true}]}\n\n'
    b'event: response.output_text.delta\ndata: {"type":"response.output_text.delta",'
    b'"delta":[{"type":"thinking","thinking":[{"type":"text","text":" said ping."}],'
    b'"closed":true}]}\n\n'
    b'event: response.output_text.delta\ndata: {"type":"response.output_text.delta",'
    b'"delta":"pong"}\n\n'
    b'event: response.output_text.done\ndata: {"type":"response.output_text.done",'
    b'"text":[{"type":"thinking","thinking":[{"type":"text","text":"x"}]}]}\n\n'
    b'event: response.completed\ndata: {"type":"response.completed"}\n\n'
)


class Upstream(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        panjang = int(self.headers.get("content-length", 0))
        self.rfile.read(panjang)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        self.wfile.write(STREAM_9ROUTER)

    def log_message(self, *a):  # noqa: ANN002
        pass


def main() -> int:
    upstream = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
    upstream.daemon_threads = True
    threading.Thread(target=upstream.serve_forever, daemon=True).start()

    server = shim.buat_server(
        port=0, base="http://127.0.0.1:%d/v1" % upstream.server_address[1],
        token="t")
    threading.Thread(target=server.serve_forever, daemon=True).start()

    url = "http://127.0.0.1:%d/v1/responses" % server.server_address[1]
    req = urllib.request.Request(
        url, data=json.dumps({"model": "deepseek-v4-pro", "stream": True,
                              "input": "ping"}).encode(), method="POST",
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        keluar = resp.read().decode()

    print("--- stream yang dilihat Codex (setelah shim) ---")
    for blok in keluar.strip().split("\n\n"):
        baris = [b for b in blok.splitlines() if b.startswith("data:")]
        if not baris:
            continue
        data = json.loads(baris[0][len("data:"):].strip())
        jenis = data.get("type")
        if jenis == "response.output_text.delta":
            print("  TEXT DELTA (str)  : %r" % data["delta"])
        elif jenis == "response.reasoning_summary_text.delta":
            print("  REASONING DELTA   : %r" % data["delta"])
        else:
            print("  %s" % jenis)

    gagal = []
    if "[object Object]" in keluar:
        gagal.append("masih ada [object Object]")
    for blok in keluar.strip().split("\n\n"):
        baris = [b for b in blok.splitlines() if b.startswith("data:")]
        if not baris:
            continue
        data = json.loads(baris[0][len("data:"):].strip())
        if data.get("type") == "response.output_text.delta" \
                and not isinstance(data.get("delta"), str):
            gagal.append("delta masih bukan string")
        if data.get("type") == "response.output_text.done" \
                and not isinstance(data.get("text"), str):
            gagal.append("text.done masih bukan string")

    upstream.shutdown()
    upstream.server_close()
    server.shutdown()
    server.server_close()

    if gagal:
        for alasan in gagal:
            print("GAGAL:", alasan)
        return 1
    print("\nOK: tidak ada '[object Object]', semua delta/text berupa string")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
