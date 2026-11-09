from __future__ import annotations

import json
import os
import re
import threading
import time
import urllib.request
from pathlib import Path
from typing import Callable
from typing import Any

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
    {"command": "health", "description": "Status bot"},
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
    parts: list[str] = []
    for key in ("product_name", "category", "brand", "buyer_sku_code"):
        parts.append(str(item.get(key, "")).lower())
    haystack = " ".join(parts)
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
PRODUCTION_BANKS = ("BCA", "MANDIRI", "BRI", "BNI", "Flip", "ShopeePay")
SANDBOX_BANKS = ("Flip", "ShopeePay")

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

def bank_keyboard(amount: int, mode: str) -> dict[str, object]:
    banks = SANDBOX_BANKS if mode == "sandbox" else PRODUCTION_BANKS
    return {
        "inline_keyboard": [
            [{"text": bank, "callback_data": f"/bank {amount} {bank}"}]
            for bank in banks
        ]
    }

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
    STATE_TTL_SECONDS = 1800

    def safe_send_message(
        self,
        chat_id: int,
        text: str,
        reply_markup: dict[str, object] | None = None,
    ) -> None:
        try:
            self.send_message(chat_id, text, reply_markup)
        except Exception as error:
            print(f"Telegram message failed: {error}", flush=True)

    def safe_answer_callback(self, callback_query_id: str) -> None:
        try:
            self.answer_callback_query(callback_query_id)
        except Exception as error:
            print(f"Telegram callback acknowledgement failed: {error}", flush=True)

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
        deposit_owner_name: str = "",
        update_offset_store: Any | None = None,
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
        self._deposit_amounts: dict[int, int] = {}
        self._deposit_banks: dict[int, tuple[int, str]] = {}
        self._state_last_seen: dict[int, float] = {}
        self.deposit_owner_name = deposit_owner_name
        self.update_offset_store = update_offset_store
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
        request = self._send_telegram_payload("/sendMessage", payload_data)
        try:
            with urllib.request.urlopen(request, timeout=30):
                pass
        except urllib.error.HTTPError:
            payload_data.pop("parse_mode", None)
            payload_data["text"] = re.sub(r"<[^>]+>", "", str(payload_data.get("text", "")))
            request = self._send_telegram_payload("/sendMessage", payload_data)
            with urllib.request.urlopen(request, timeout=30):
                pass

    def _send_telegram_payload(self, method: str, payload_data: dict[str, object]) -> urllib.request.Request:
        payload = json.dumps(payload_data).encode("utf-8")
        return urllib.request.Request(
            f"{self.api_base_url}/bot{self.token}/{method.lstrip('/')}",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

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
            self.safe_answer_callback(query_id)

    def _handle_text(self, chat_id: int, text: str) -> None:
        command, args = self._command(text)
        self.touch_state(chat_id)
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
            if command.isdigit() and chat_id in self._deposit_amounts:
                amount = int(command)
                if amount < 200_000:
                    self.send_message(chat_id, "Minimal deposit Digiflazz adalah Rp 200.000.")
                    return
                del self._deposit_amounts[chat_id]
                self.send_message(
                    chat_id,
                    f"<b>Pilih Bank</b>\n\nDeposit: <b>{TelegramStoreService.format_rupiah(amount)}</b>",
                    bank_keyboard(amount, getattr(self, "mode", "prod")),
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
                self.safe_send_message(chat_id, "⏳ <b>Memproses pesanan…</b>")
                order = self.service.order(str(product["buyer_sku_code"]), text.strip())
                del self._selected_products[chat_id]
                result_sent = False
                try:
                    self.send_message(
                        chat_id,
                        "<b>Pesanan Dibuat</b>\n\n"
                        f"Invoice: <code>{order['invoice']}</code>\n"
                        f"Produk: <b>{order['product']}</b>\n"
                        f"Status: <b>{order['status']}</b>\n\n"
                        "Gunakan <code>/status " + str(order['invoice']) + "</code> untuk memantau.",
                    )
                    result_sent = True
                except Exception as error:
                    print(f"Telegram message failed: {error}", flush=True)
                if not result_sent:
                    self._selected_products[chat_id] = product
                    self.safe_send_message(chat_id, "⚠️ Pesanan sudah dibuat, tetapi pesan gagal dikirim. Kirim <code>/status " + str(order['invoice']) + "</code> untuk memantau.")
                return
            if command == "nominal":
                self._deposit_amounts[chat_id] = 0
                self.send_message(
                    chat_id,
                    "Kirim nominal deposit.\nMinimal <b>Rp 200.000</b>.",
                )
                return
            if command.isdigit() and chat_id in self._deposit_amounts:
                amount = int(command)
                if amount < 200_000:
                    self.send_message(chat_id, "Minimal deposit Digiflazz adalah Rp 200.000.")
                    return
                del self._deposit_amounts[chat_id]
                self.send_message(
                    chat_id,
                    f"<b>Pilih Bank</b>\n\nDeposit: <b>{TelegramStoreService.format_rupiah(amount)}</b>",
                    bank_keyboard(amount, getattr(self, "mode", "prod")),
                )
                return
            if not text.strip().startswith("/") and chat_id in self._deposit_banks:
                amount, bank = self._deposit_banks[chat_id]
                owner_name = self.deposit_owner_name or text.strip()
                if owner_name:
                    del self._deposit_banks[chat_id]
                    ticket = self.service.create_deposit(amount, bank, owner_name)
                    self.send_message(chat_id, format_deposit_ticket(ticket, amount))
                return
            if command in {"start", "help", "bantuan"}:
                self.send_message(
                    chat_id,
                    f"Selamat datang di {self.bot_username}. Silakan pilih menu:",
                    reply_markup=MENU_KEYBOARD,
                )
            elif command in {"produk", "product"}:
                self.safe_send_message(chat_id, "⏳ <b>Memuat produk…</b>")
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
                self.safe_send_message(chat_id, "⏳ <b>Memproses pesanan…</b>")
                order = self.service.order(args[0], " ".join(args[1:]))
                self.send_message(
                    chat_id,
                    "<b>Pesanan Dibuat</b>\n\n"
                    f"Invoice: <code>{order['invoice']}</code>\n"
                    f"Produk: <b>{order['product']}</b>\n"
                    f"Status: <b>{order['status']}</b>\n\n"
                    "Gunakan <code>/status " + str(order['invoice']) + "</code> untuk memantau.",
                )
            elif command in {"status", "cekstatus"}:
                if not args:
                    self.send_message(chat_id, "Format: /status <invoice>")
                    return
                self.safe_send_message(chat_id, "⏳ <b>Memeriksa status…</b>")
                order = self.service.status(args[0])
                self.safe_send_message(
                    chat_id,
                    "<b>Status Transaksi</b>\n\n"
                    f"Invoice: <code>{order['invoice']}</code>\n"
                    f"Status: <b>{order['status']}</b>\n"
                    f"Pesan: {order['message']}",
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
                    ] + [[{"text": "Input Nominal", "callback_data": "/nominal"}]]
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
            elif command == "health":
                try:
                    balance = self.service.digiflazz.balance()
                    digiflazz_status = "OK"
                except Exception:
                    digiflazz_status = "Gagal"
                    balance = 0
                try:
                    product_count = len(self.service.catalog.get_all()) if self.service.catalog else 0
                except Exception:
                    product_count = 0
                mode_label = "Production" if getattr(self, "mode", "prod") == "prod" else "Sandbox"
                try:
                    offset = int(self.update_offset_store.get_update_offset()) if self.update_offset_store else None
                    state_status = "OK" if self.update_offset_store else "Belum aktif"
                except Exception:
                    state_status = "Gagal"
                    offset = None
                try:
                    db_integrity = (
                        str(self.update_offset_store.connection.execute("PRAGMA integrity_check").fetchone()[0]).upper()
                        if self.update_offset_store else None
                    )
                except Exception:
                    db_integrity = None
                integrity_status = "OK" if db_integrity == "OK" else (db_integrity or "Belum aktif")
                cache_line = f"Cache produk: <b>{product_count} produk</b>"
                state_lines = f"State DB: <b>{state_status}</b>"
                state_lines += f"\nIntegritas DB: <b>{integrity_status}</b>"
                if offset is not None:
                    state_lines += f"\nUpdate offset: <code>{offset}</code>"
                self.send_message(
                    chat_id,
                    "<b>Status Bot</b>\n\n"
                    "Polling: <b>OK</b>\n"
                    f"Digiflazz: <b>{digiflazz_status}</b>\n"
                    f"Saldo: <code>{TelegramStoreService.format_rupiah(balance)}</code>\n"
                    f"Mode: <b>{mode_label}</b>\n"
                    f"{cache_line}\n"
                    f"{state_lines}",
                )
            elif command == "prod":
                self.mode = "prod"
                self._selected_products.clear()
                self._deposit_amounts.clear()
                self._deposit_banks.clear()
                self.service.digiflazz.set_mode("prod")
                self.service.testing = False
                self.send_message(chat_id, "<b>Mode Production aktif.</b>\nSemua transaksi akan diproses nyata.")
            elif command == "sandbox":
                self.mode = "sandbox"
                self._selected_products.clear()
                self._deposit_amounts.clear()
                self._deposit_banks.clear()
                self.service.digiflazz.set_mode("sandbox")
                self.service.testing = True
                self.send_message(chat_id, "<b>Mode Sandbox aktif.</b>\nTransaksi ditandai testing=True.")
            elif command == "bank":
                amount = int(args[0])
                bank = args[1].upper() if args[1].lower() in {"bca", "mandiri", "bri", "bni"} else args[1].title()
                if bank.lower() == "shopeepay":
                    bank = "ShopeePay"
                if self.deposit_owner_name:
                    ticket = self.service.create_deposit(amount, bank, self.deposit_owner_name)
                    self.send_message(chat_id, format_deposit_ticket(ticket, amount))
                else:
                    self._deposit_banks[chat_id] = (amount, bank)
                    self.send_message(
                        chat_id,
                        f"<b>Deposit {TelegramStoreService.format_rupiah(amount)}</b>\n\n"
                        f"Bank: <b>{bank}</b>\n"
                        "Kirim nama pemilik rekening.",
                    )
                return
            elif command == "isidaldo":
                amount = int(args[0]) if args else 0
                if amount < 200_000:
                    self.send_message(chat_id, "Minimal deposit Digiflazz adalah Rp 200.000.")
                    return
                if len(args) == 1:
                    self._deposit_amounts[chat_id] = amount
                    self.send_message(
                        chat_id,
                        f"<b>Pilih Bank</b>\n\nDeposit: <b>{TelegramStoreService.format_rupiah(amount)}</b>",
                        bank_keyboard(amount, getattr(self, "mode", "prod")),
                    )
                    return
                if len(args) == 2:
                    bank = args[1].upper() if args[1].lower() in {"bca", "mandiri", "bri", "bni"} else args[1].title()
                    if bank.lower() == "shopeepay":
                        bank = "ShopeePay"
                    self._deposit_banks[chat_id] = (amount, bank)
                    self.send_message(
                        chat_id,
                        f"<b>Deposit {TelegramStoreService.format_rupiah(amount)}</b>\n\n"
                        f"Bank: <b>{bank}</b>\n"
                        "Kirim nama pemilik rekening.",
                    )
                    return
                ticket = self.service.create_deposit(amount, args[1].upper() if args[1].lower() in {"bca", "mandiri", "bri", "bni"} else (args[1].title().replace("Shopeepay", "ShopeePay")), " ".join(args[2:]))
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
        except RuntimeError as error:
            self.send_message(chat_id, f"Digiflazz gagal diproses: {error}")
        except urllib.error.URLError as error:
            self.send_message(chat_id, f"Digiflazz gagal diproses: {error.reason}")

    def touch_state(self, chat_id: int, now: float | None = None) -> float:
        timestamp = time.monotonic() if now is None else now
        self._state_last_seen[chat_id] = timestamp
        return timestamp

    def cleanup_expired_state(self, now: float | None = None) -> None:
        current = time.monotonic() if now is None else now
        expired = [
            chat_id
            for chat_id, seen_at in self._state_last_seen.items()
            if current - seen_at >= self.STATE_TTL_SECONDS
        ]
        for chat_id in expired:
            self._catalog_numbers.pop(chat_id, None)
            self._selected_products.pop(chat_id, None)
            self._deposit_amounts.pop(chat_id, None)
            self._deposit_banks.pop(chat_id, None)
            self._state_last_seen.pop(chat_id, None)

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
        try:
            self.set_my_commands()
        except Exception as error:
            print(f"Telegram command setup failed: {error}", flush=True)
        offset = int(self.update_offset_store.get_update_offset()) if self.update_offset_store else 0
        while True:
            try:
                updates = self.get_updates(offset)
            except KeyboardInterrupt:
                break
            except SystemExit as error:
                print(f"Telegram polling fatal failure, restarting loop: {error}", flush=True)
                time.sleep(1)
                continue
            except Exception as error:
                print(f"Telegram polling failed: {error}", flush=True)
                time.sleep(1)
                continue
            if not isinstance(updates, list):
                print(f"Telegram polling returned invalid payload: {type(updates).__name__}", flush=True)
                continue
            self.cleanup_expired_state()
            for update in updates:
                if not isinstance(update, dict):
                    print("Telegram polling skipped invalid update payload", flush=True)
                    continue
                try:
                    update_id = int(update.get("update_id", 0))
                except (TypeError, ValueError):
                    print("Telegram polling skipped invalid update id", flush=True)
                    continue
                offset = max(offset, update_id + 1)
                if self.update_offset_store:
                    try:
                        self.update_offset_store.set_update_offset(offset)
                    except Exception as error:
                        print(f"Telegram offset state failed: {error}", flush=True)
                try:
                    self.handle_update(update)
                except urllib.error.HTTPError as error:
                    print(f"Telegram update failed: HTTP {error.code}", flush=True)
                    if self.update_offset_store and hasattr(self.update_offset_store, "record_update_error"):
                        try:
                            self.update_offset_store.record_update_error(update_id, f"HTTP {error.code}", update)
                        except Exception as record_error:
                            print(f"Telegram update error persistence failed: {record_error}", flush=True)
                except Exception as error:
                    print(f"Telegram update failed: {error}", flush=True)
                    if self.update_offset_store and hasattr(self.update_offset_store, "record_update_error"):
                        try:
                            self.update_offset_store.record_update_error(update_id, str(error), update)
                        except Exception as record_error:
                            print(f"Telegram update error persistence failed: {record_error}", flush=True)
