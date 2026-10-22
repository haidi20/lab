from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path
from typing import Callable

from .service import TelegramStoreService

BOT_COMMANDS = [
    {"command": "start", "description": "Mulai bot"},
    {"command": "bantuan", "description": "Bantuan penggunaan"},
    {"command": "produk", "description": "Lihat daftar produk"},
    {"command": "beli", "description": "Beli produk"},
    {"command": "cekstatus", "description": "Cek status transaksi"},
]

MENU_KEYBOARD = {
    "inline_keyboard": [
        [
            {"text": "Lihat Produk", "callback_data": "/produk"},
            {"text": "Beli Produk", "callback_data": "/beli"},
        ],
        [{"text": "Cek Status", "callback_data": "/cekstatus"}],
    ]
}


def load_env_file(path: str | Path = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


class TelegramStoreBot:
    def __init__(
        self,
        token: str,
        service: TelegramStoreService,
        bot_username: str = "@hn_assistent_bot",
        send_message: Callable[..., None] | None = None,
        answer_callback_query: Callable[[str], None] | None = None,
        api_base_url: str = "https://api.telegram.org",
    ) -> None:
        self.token = token
        self.service = service
        self.bot_username = bot_username
        self.api_base_url = api_base_url.rstrip("/")
        self.send_message = send_message or self._send_message
        self.answer_callback_query = answer_callback_query or self._answer_callback_query

    def _send_message(
        self,
        chat_id: int,
        text: str,
        reply_markup: dict[str, object] | None = None,
    ) -> None:
        payload_data: dict[str, object] = {"chat_id": chat_id, "text": text}
        if reply_markup is not None:
            payload_data["reply_markup"] = reply_markup
        payload = json.dumps(payload_data).encode("utf-8")
        request = urllib.request.Request(
            f"{self.api_base_url}/bot{self.token}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30):
            pass

    def _answer_callback_query(self, callback_query_id: str) -> None:
        payload = json.dumps({"callback_query_id": callback_query_id}).encode("utf-8")
        request = urllib.request.Request(
            f"{self.api_base_url}/bot{self.token}/answerCallbackQuery",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30):
            pass

    @staticmethod
    def _command(text: str) -> tuple[str, list[str]]:
        parts = text.strip().split()
        if not parts:
            return "", []
        return parts[0].split("@", 1)[0].lstrip("/").lower(), parts[1:]

    def handle_update(self, update: dict[str, object]) -> None:
        callback = update.get("callback_query")
        if isinstance(callback, dict):
            self._handle_callback(callback)
            return
        message = update.get("message")
        if not isinstance(message, dict):
            return
        chat = message.get("chat")
        text = message.get("text", "")
        if not isinstance(chat, dict) or not isinstance(text, str):
            return

        self._handle_text(int(chat.get("id", 0)), text)

    def _handle_callback(self, callback: dict[str, object]) -> None:
        data = callback.get("data")
        message = callback.get("message")
        if isinstance(data, str) and isinstance(message, dict):
            chat = message.get("chat")
            if isinstance(chat, dict):
                self._handle_text(int(chat.get("id", 0)), data)
        query_id = callback.get("id")
        if isinstance(query_id, str):
            self.answer_callback_query(query_id)

    def _handle_text(self, chat_id: int, text: str) -> None:
        command, args = self._command(text)
        try:
            if command in {"start", "help", "bantuan"}:
                self.send_message(
                    chat_id,
                    f"Selamat datang di {self.bot_username}. Silakan pilih menu:",
                    reply_markup=MENU_KEYBOARD,
                )
            elif command in {"produk", "product"}:
                products = self.service.list_products(" ".join(args))
                if not products:
                    self.send_message(chat_id, "Produk tidak ditemukan.")
                    return
                lines = [
                    f"{item['buyer_sku_code']} - {item['product_name']} "
                    f"({self.service.format_rupiah(int(item['sale_price']))})"
                    for item in products
                ]
                self.send_message(chat_id, "\n".join(lines))
            elif command == "beli":
                if len(args) < 2:
                    self.send_message(chat_id, "Format: /beli <SKU> <nomor/id tujuan>")
                    return
                order = self.service.order(args[0], " ".join(args[1:]))
                self.send_message(
                    chat_id,
                    f"Pesanan dibuat.\nInvoice: {order['invoice']}\n"
                    f"Produk: {order['product']}\nStatus: {order['status']}",
                )
            elif command in {"status", "cekstatus"}:
                if not args:
                    self.send_message(chat_id, "Format: /status <invoice>")
                    return
                order = self.service.status(args[0])
                self.send_message(
                    chat_id,
                    f"Invoice: {order['invoice']}\nStatus: {order['status']}\nPesan: {order['message']}",
                )
            elif command == "saldo":
                self.send_message(
                    chat_id,
                    "Fitur saldo belum tersedia.",
                )
            else:
                self.send_message(chat_id, "Perintah tidak dikenal. Gunakan /help.")
        except (KeyError, ValueError) as error:
            self.send_message(chat_id, f"Gagal: {error}")

    def get_updates(self, offset: int = 0) -> list[dict[str, object]]:
        url = f"{self.api_base_url}/bot{self.token}/getUpdates?offset={offset}&timeout=25"
        with urllib.request.urlopen(url, timeout=35) as response:
            result = json.loads(response.read().decode("utf-8")).get("result", [])
        return result if isinstance(result, list) else []

    def set_my_commands(self) -> None:
        payload = json.dumps({"commands": BOT_COMMANDS}).encode("utf-8")
        request = urllib.request.Request(
            f"{self.api_base_url}/bot{self.token}/setMyCommands",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30):
            pass

    def run(self) -> None:
        self.set_my_commands()
        offset = 0
        while True:
            for update in self.get_updates(offset):
                update_id = int(update.get("update_id", 0))
                offset = max(offset, update_id + 1)
                self.handle_update(update)
