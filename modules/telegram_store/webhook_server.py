from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .service import TelegramStoreService


class WebhookHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


class WebhookServer:
    def __init__(
        self,
        server_address: tuple[str, int],
        service: TelegramStoreService,
        signature_header: str = "X-Digiflazz-Sign",
    ) -> None:
        self.service = service
        self.signature_header = signature_header
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                if self.path != "/health":
                    self._json(404, {"ok": False})
                    return
                self._json(200, {"ok": True, "service": "telegram-store"})

            def do_POST(self) -> None:
                if self.path != "/webhook/digiflazz":
                    self._json(404, {"ok": False})
                    return
                try:
                    content_length = int(self.headers.get("Content-Length", "0"))
                    payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
                except Exception:
                    self._json(400, {"ok": False, "error": "invalid_json"})
                    return
                if not isinstance(payload, dict):
                    self._json(400, {"ok": False, "error": "invalid_payload"})
                    return
                signature = self.headers.get(outer.signature_header)
                try:
                    updated = outer.service.apply_webhook(payload, signature=signature)
                except Exception:
                    self._json(500, {"ok": False, "error": "webhook_failed"})
                    return
                if updated:
                    self._json(200, {"ok": True, "updated": True})
                    return
                if not signature:
                    self._json(401, {"ok": False, "error": "missing_signature"})
                    return
                if outer.service.verify_signature(signature, str(payload.get("ref_id", ""))) is False:
                    self._json(401, {"ok": False, "error": "invalid_signature"})
                    return
                invoices = {str(order.get("invoice", "")) for order in outer.service.orders.find_all()}
                if str(payload.get("ref_id", "")) not in invoices:
                    self._json(404, {"ok": False, "error": "unknown_invoice"})
                    return
                self._json(200, {"ok": True, "updated": False})

            def _json(self, status: int, body: dict[str, Any]) -> None:
                data = json.dumps(body, sort_keys=True).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, format: str, *args: object) -> None:
                print(f"Webhook: {format % args}", flush=True)

        self.httpd = WebhookHTTPServer(server_address, Handler)

    @property
    def server_address(self) -> tuple[str, int]:
        return self.httpd.server_address[:2]

    def serve_forever(self) -> None:
        self.httpd.serve_forever()

    def shutdown(self) -> None:
        self.httpd.shutdown()

    def server_close(self) -> None:
        self.httpd.server_close()


def build_webhook_server_from_env() -> WebhookServer:
    from .cli import build_bot_from_env

    bot = build_bot_from_env()
    return WebhookServer(
        ("0.0.0.0", int(os.environ.get("TELEGRAM_STORE_WEBHOOK_PORT", "8110"))),
        bot.service,
        os.environ.get("DIGIFLAZZ_WEBHOOK_SIGNATURE_HEADER", "X-Digiflazz-Sign"),
    )


def main() -> None:
    server = build_webhook_server_from_env()
    print("Telegram Store webhook listening", server.server_address, flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
