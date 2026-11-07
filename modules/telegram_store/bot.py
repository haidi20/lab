from __future__ import annotations

import json
import os
import re
import threading
import time
import urllib.request
from pathlib import Path
from typing import Callable

from .service import TelegramStoreService
from .hermes_status import HermesStatusProvider
from .hermes_chat import HermesChatClient

BOT_COMMANDS = [
    {"command": "start", "description": "Mulai bot"},
    {"command": "produk", "description": "Daftar produk"},
    {"command": "beli", "description": "Beli produk"},
    {"command": "cekstatus", "description": "Cek status transaksi"},
    {"command": "saldo", "description": "Isi saldo"},
    {"command": "mode", "description": "Lihat mode transaksi"},
    {"command": "prod", "description": "Aktifkan mode produksi"},
    {"command": "sandbox", "description": "Aktifkan mode sandbox"},
]
BOT_COMMANDS.insert(1, {'command': 'perintah', 'description': 'Daftar perintah bot'})

MENU_KEYBOARD = {
    "inline_keyboard": [
        [{"text": "Mulai", "callback_data": "/start"}],
        [
            {"text": "Daftar Produk", "callback_data": "/produk"},
            {"text": "Beli Produk", "callback_data": "/beli"},
        ],
        [{"text": "Cek Status", "callback_data": "/cekstatus"}],
        [{"text": "Isi Saldo", "callback_data": "/saldo"}],
        [
            {"text": "Mode Transaksi", "callback_data": "/mode"},
            {"text": "Prod", "callback_data": "/prod"},
            {"text": "Sandbox", "callback_data": "/sandbox"},
        ],
        [{"text": "Daftar Perintah", "callback_data": "/perintah"}],
    ],
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

def format_product_list(products: list[dict[str, object]]) -> str:
    lines = ["<b>Daftar Produk</b>", ""]
    for index, item in enumerate(products, start=1):
        brand = str(item.get("brand", "") or item.get("seller_name", ""))
        category = str(item.get("category", ""))
        lines.extend(
            [
                f"{index}. <b>{item['product_name']}</b>",
                f"   {brand} • {category}",
                f"   <code>{item['buyer_sku_code']}</code> • "
                f"{TelegramStoreService.format_rupiah(int(item['sale_price']))}",
                "",
            ]
        )
    lines.append("Pilih berdasarkan nomor produk.")
    return "\n".join(lines)

def product_priority(item: dict[str, object]) -> tuple[int, str]:
    haystack = " ".join(
        str(item.get(key, "")).lower()
        for key in ("product_name", "category", "brand", "buyer_sku_code")
    )
    if "pln" in haystack:
        return (0, str(item.get("product_name", "")).lower())
    if "pdam" in haystack or " air " in f" {haystack} ":
        return (1, str(item.get("product_name", "")).lower())
    if str(item.get("brand", "")).lower() == "telkomsel":
        return (2, str(item.get("product_name", "")).lower())
    return (3, str(item.get("product_name", "")).lower())

def product_keyboard(products: list[dict[str, object]]) -> dict[str, object]:
    ordered = sorted(products, key=product_priority)
    rows = [
        [{"text": str(item["product_name"]), "callback_data": f"/pilih {item['buyer_sku_code']}"}]
        for item in ordered
    ]
    return {"inline_keyboard": rows}

DEPOSIT_NOMINALS = (200_000, 500_000, 1_000_000, 2_000_000)

def format_deposit_menu(balance: int, mode: str = "prod") -> str:
    mode_label = "Production" if mode == "prod" else "Sandbox"
    nominal_lines = "\n".join(
        f"• Rp {nominal:,.0f}".replace(",", ".")
        for nominal in DEPOSIT_NOMINALS
    )
    return (
        "<b>Isi Saldo</b>\n\n"
        f"Mode: <b>{mode_label}</b>\n"
        f"Saldo saat ini: <code>{TelegramStoreService.format_rupiah(balance)}</code>\n\n"
        "Pilih nominal deposit:\n"
        f"{nominal_lines}\n\n"
        "Minimal deposit Digiflazz adalah Rp 200.000."
    )

def format_deposit_instruction(amount: int) -> str:
    return (
        f"<b>Deposit {TelegramStoreService.format_rupiah(amount)}</b>\n\n"
        "Kirim format berikut:\n"
        f"<code>/isidaldo {amount} BCA Nama Pemilik Rekening</code>\n\n"
        "Bank yang didukung:\n"
        "• Perorangan: <code>Flip</code>, <code>ShopeePay</code>\n"
        "• Perusahaan: <code>BCA</code>, <code>MANDIRI</code>, <code>BRI</code>, <code>BNI</code>"
    )

def format_deposit_ticket(deposit: dict[str, object], amount: int) -> str:
    final_amount = int(deposit.get("amount", amount))
    account_no = re.sub(r"[\s-]", "", str(deposit.get("account_no", "")))
    return (
        "<b>Tiket Deposit Dibuat</b>\n\n"
        f"Metode: <b>{deposit.get('payment_method', '-')}</b>\n"
        f"Bank: <code>{deposit.get('bank', '-')}</code>\n"
        f"Nomor: <code>{account_no or '-'}</code>\n"
        f"Nominal transfer: <code>{TelegramStoreService.format_rupiah(final_amount)}</code>\n"
        f"Berita transfer: <code>{deposit.get('notes', '-')}</code>\n\n"
        "Transfer tepat sesuai nominal dan isi berita transfer di atas."
    )


class TelegramStoreBot:
    def __init__(
        self,
        token: str,
        service: TelegramStoreService,
        bot_username: str = "@hn_assistent_bot",
        send_message: Callable[..., None] | None = None,
        answer_callback_query: Callable[[str], None] | None = None,
        api_base_url: str = "https://api.telegram.org",
        hermes_status: HermesStatusProvider | None = None,
        hermes_chat: HermesChatClient | None = None,
        live_interval: float = 20.0,
        live_max_updates: int | None = None,
        live_duration_seconds: float = 60.0,
        mode: str = "prod",
    ) -> None:
        self.token = token
        self.service = service
        self.bot_username = bot_username
        self.api_base_url = api_base_url.rstrip("/")
        self.send_message = send_message or self._send_message
        self.answer_callback_query = answer_callback_query or self._answer_callback_query
        self.hermes_status = hermes_status
        self.hermes_chat = hermes_chat
        self.live_interval = live_interval
        self.live_max_updates = live_max_updates
        self.live_duration_seconds = live_duration_seconds
        self._hermes_live: dict[int, threading.Event] = {}
        self._hermes_chat_busy: set[int] = set()
        self._hermes_chat_pending: dict[int, str] = {}
        self._hermes_chat_sessions: set[int] = set()
        self._selected_products: dict[int, dict[str, object]] = {}
        self._catalog_numbers: dict[int, list[dict[str, object]]] = {}
        self.mode = mode
        self.service.testing = mode == "sandbox"

    def _send_message(
        self,
        chat_id: int,
        text: str,
        reply_markup: dict[str, object] | None = None,
    ) -> None:
        payload_data: dict[str, object] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        }
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
            if command.isdigit() and chat_id in self._catalog_numbers:
                index = int(text.strip()) - 1
                catalog = self._catalog_numbers[chat_id]
                if 0 <= index < len(catalog):
                    product = catalog[index]
                    self._selected_products[chat_id] = product
                    self.send_message(
                        chat_id,
                        f"Produk dipilih: <b>{product['product_name']}</b>\n"
                        f"SKU: <code>{product['buyer_sku_code']}</code>\n"
                        f"Harga: <code>{TelegramStoreService.format_rupiah(int(product.get('sale_price', product.get('price', 0))))}</code>\n\n"
                        "Kirim nomor tujuan sekarang.",
                    )
                    return
            if command == 'perintah':
                self.send_message(
                    chat_id,
                    f'Selamat datang di {self.bot_username}. Silakan pilih menu:',
                    reply_markup=MENU_KEYBOARD,
                )
                return
            if not text.strip().startswith("/") and chat_id in self._hermes_chat_sessions:
                self._contact_hermes(chat_id, text.strip())
                return
            if not text.strip().startswith("/") and chat_id in self._selected_products:
                product = self._selected_products[chat_id]
                order = self.service.order(str(product["buyer_sku_code"]), text.strip())
                del self._selected_products[chat_id]
                self.send_message(
                    chat_id,
                    f"Pesanan dibuat.\nInvoice: {order['invoice']}\n"
                    f"Produk: {order['product']}\nStatus: {order['status']}",
                )
                return
            if command in {"start", "help", "bantuan"}:
                self.send_message(
                    chat_id,
                    f"Selamat datang di {self.bot_username}. Silakan pilih menu:",
                    reply_markup=MENU_KEYBOARD,
                )
            elif command in {"produk", "product"}:
                products = self.service.list_products(" ".join(args))
                self._catalog_numbers[chat_id] = sorted(products, key=product_priority)
                if not products:
                    self.send_message(chat_id, "Produk tidak ditemukan.")
                    return
                self.send_message(chat_id, format_product_list(products), product_keyboard(products))
            elif command == "pilih":
                matches = self.service.digiflazz.price_list(args[0])
                if not matches:
                    self.send_message(chat_id, "Produk tidak ditemukan.")
                    return
                product = matches[0]
                self._selected_products[chat_id] = product
                self.send_message(
                    chat_id,
                    f"Produk dipilih: <b>{product['product_name']}</b>\n"
                    f"SKU: <code>{product['buyer_sku_code']}</code>\n"
                    f"Harga: <code>{TelegramStoreService.format_rupiah(int(product.get('price', 0)))}</code>\n\n"
                    "Kirim nomor tujuan sekarang.",
                )
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
                balance = self.service.digiflazz.balance()
                mode = getattr(self, "mode", "prod")
                nominal_keyboard = {
                    "inline_keyboard": [
                        [
                            {"text": f"Rp {nominal:,.0f}".replace(",", "."), "callback_data": f"/isidaldo {nominal}"},
                        ]
                        for nominal in DEPOSIT_NOMINALS
                    ]
                }
                self.send_message(chat_id, format_deposit_menu(balance, mode), nominal_keyboard)
            elif command == "mode":
                mode = getattr(self, "mode", "prod")
                mode_label = "Production" if mode == "prod" else "Sandbox"
                self.send_message(
                    chat_id,
                    f"<b>Mode Transaksi</b>\n\nMode saat ini: <b>{mode_label}</b>\n\n"
                    "Gunakan <code>/prod</code> untuk production dan <code>/sandbox</code> untuk pengujian.",
                )
            elif command == "prod":
                self.mode = "prod"
                self.service.digiflazz.set_mode("prod")
                self.service.testing = False
                self.send_message(chat_id, "<b>Mode Production aktif.</b>\nSemua transaksi akan diproses nyata.")
            elif command == "sandbox":
                self.mode = "sandbox"
                self.service.digiflazz.set_mode("sandbox")
                self.service.testing = True
                self.send_message(chat_id, "<b>Mode Sandbox aktif.</b>\nTransaksi ditandai testing=True.")
            elif command == "isidaldo":
                amount = int(args[0]) if args else 0
                if len(args) == 1:
                    self.send_message(chat_id, format_deposit_instruction(amount))
                    return
                if len(args) < 3:
                    self.send_message(chat_id, "Format: /isidaldo <nominal> <bank> <nama pemilik rekening>")
                    return
                ticket = self.service.create_deposit(amount, args[1].upper(), " ".join(args[2:]))
                self.send_message(chat_id, format_deposit_ticket(ticket, amount))
            elif command in {"hermes", "starthermes", "statushermes"}:
                if self.hermes_status is None:
                    self.send_message(chat_id, "Status Hermes belum tersedia.")
                else:
                    self.send_message(chat_id, self.hermes_status.summary())
            elif command in {"hermeslive", "livehermes"}:
                self._start_hermes_live(chat_id)
            elif command in {"hermesstop", "stophermes"}:
                self._stop_hermes_live(chat_id)
            elif command in {"hubungihermes", "tanyahermes"}:
                if self.hermes_chat is None:
                    self.send_message(chat_id, "Hermes belum tersedia.")
                    return
                self._hermes_chat_sessions.add(chat_id)
                if not args:
                    self.send_message(chat_id, "Mode komunikasi Hermes aktif. Kirim pesan biasa; gunakan /akhirihermes untuk berhenti.")
                else:
                    self._contact_hermes(chat_id, " ".join(args))
            elif command in {"akhirihermes", "tutuphermes"}:
                if chat_id not in self._hermes_chat_sessions:
                    self.send_message(chat_id, "Mode komunikasi Hermes tidak aktif.")
                else:
                    self._hermes_chat_sessions.discard(chat_id)
                    self.send_message(chat_id, "Mode komunikasi Hermes diakhiri.")
            else:
                self.send_message(chat_id, "Perintah tidak dikenal. Gunakan /help.")
        except (KeyError, ValueError) as error:
            self.send_message(chat_id, f"Gagal: {error}")

    def _start_hermes_live(self, chat_id: int) -> None:
        if self.hermes_status is None:
            self.send_message(chat_id, "Status Hermes belum tersedia.")
            return
        if chat_id in self._hermes_live:
            self.send_message(chat_id, "Monitoring Hermes live sudah aktif.")
            return

        stop_event = threading.Event()
        self._hermes_live[chat_id] = stop_event
        thread = threading.Thread(
            target=self._run_hermes_live,
            args=(chat_id, stop_event),
            daemon=True,
        )
        self.send_message(chat_id, "Monitoring Hermes live aktif selama 1 menit. Update dikirim saat ada perubahan.")
        thread.start()

    def _stop_hermes_live(self, chat_id: int) -> None:
        stop_event = self._hermes_live.pop(chat_id, None)
        if stop_event is None:
            self.send_message(chat_id, "Monitoring Hermes live tidak aktif.")
            return
        stop_event.set()
        self.send_message(chat_id, "Monitoring Hermes live dihentikan.")

    def _run_hermes_live(self, chat_id: int, stop_event: threading.Event) -> None:
        last_summary: str | None = None
        updates = 0
        started_at = time.monotonic()
        expired = False
        try:
            while not stop_event.is_set():
                remaining = self.live_duration_seconds - (time.monotonic() - started_at)
                if remaining <= 0:
                    expired = True
                    break
                try:
                    summary = self.hermes_status.summary() if self.hermes_status else "Status Hermes belum tersedia."
                except Exception as error:
                    summary = f"Status Hermes gagal dimuat: {error}"
                if summary != last_summary:
                    self.send_message(chat_id, summary)
                    last_summary = summary
                updates += 1
                if self.live_max_updates is not None and updates >= self.live_max_updates:
                    expired = True
                    break
                if stop_event.wait(min(self.live_interval, remaining)):
                    break
            if expired and not stop_event.is_set():
                self.send_message(chat_id, "Sesi monitoring Hermes 1 menit selesai.")
        finally:
            if self._hermes_live.get(chat_id) is stop_event:
                self._hermes_live.pop(chat_id, None)

    def _contact_hermes(self, chat_id: int, question: str) -> None:
        if self.hermes_chat is None:
            self.send_message(chat_id, "Hermes belum tersedia.")
            return
        if chat_id in self._hermes_chat_busy:
            self._hermes_chat_pending[chat_id] = question
            self.send_message(
                chat_id,
                "Hermes sedang menjawab pertanyaan sebelumnya. Pesan ini akan dikirim setelah selesai.",
            )
            return

        self._hermes_chat_busy.add(chat_id)
        self.send_message(chat_id, "Menghubungi Hermes...")
        thread = threading.Thread(
            target=self._run_hermes_chat,
            args=(chat_id, question),
            daemon=True,
        )
        thread.start()

    def _run_hermes_chat(self, chat_id: int, question: str) -> None:
        try:
            answer = self.hermes_chat.ask(question) if self.hermes_chat else "Hermes belum tersedia."
            self.send_message(chat_id, answer)
        except Exception as error:
            self.send_message(chat_id, f"Gagal menghubungi Hermes: {error}")
        finally:
            self._hermes_chat_busy.discard(chat_id)
            pending_question = self._hermes_chat_pending.pop(chat_id, None)
        if pending_question:
            self._contact_hermes(chat_id, pending_question)

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
