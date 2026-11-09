from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import threading
import time
from unittest.mock import patch
from pathlib import Path
import tempfile
import unittest

from modules.telegram_store import (
    DigiflazzClient,
    InMemoryOrderStore,
    TelegramStoreBot,
    TelegramStoreService,
    load_env_file,
)
from modules.telegram_store.cli import _post_provider, _run_hermes_command, build_bot_from_env
from modules.telegram_store.hermes_status import HermesStatusProvider
from modules.telegram_store.hermes_chat import HermesChatClient
from modules.telegram_store.bot import BOT_COMMANDS, MENU_KEYBOARD, format_deposit_menu


class FakeTransport:
    def __init__(self, responses: dict[tuple[str, str], dict[str, object]]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def __call__(self, method: str, url: str, payload: dict[str, object]) -> dict[str, object]:
        self.calls.append((method, url, payload))
        key = (method, url)
        if key not in self.responses:
            raise AssertionError(f"Unexpected request: {method} {url}")
        return self.responses[key]


class FakeDigiflazz:
    def __init__(self, balance: int = 250_000) -> None:
        self.orders: list[tuple[str, str, str]] = []
        self.status_requests: list[tuple[str, str, str]] = []
        self.status_responses: list[dict[str, object]] = []
        self.balance_value = balance

    def balance(self) -> int:
        return self.balance_value

    def create_deposit(self, amount: int, bank: str, owner_name: str) -> dict[str, object]:
        self.deposit_request = (amount, bank, owner_name)
        return {
            "rc": "00",
            "bank": "ShopeePay",
            "payment_method": "Virtual Account",
            "account_no": "0123 4567 89",
            "amount": amount + 1,
            "notes": "A6R5UPV",
        }

    def set_mode(self, mode: str) -> None:
        self.mode_set = mode

    def price_list(self, code: str | None = None) -> list[dict[str, object]]:
        products = [
            {
                "buyer_sku_code": "BRIZZI5",
                "product_name": "Brizzi 5",
                "category": "E-Money",
                "brand": "BRIZZI",
                "seller_name": "Digiflazz",
                "price": 6_200,
                "buyer_product_status": True,
                "seller_product_status": True,
            },
            {
                "buyer_sku_code": "PLN100",
                "product_name": "Token PLN 100",
                "category": "PLN",
                "brand": "PLN",
                "seller_name": "Digiflazz",
                "price": 11_500,
                "buyer_product_status": True,
                "seller_product_status": True,
            },
        ]
        if code:
            return [item for item in products if item["buyer_sku_code"] == code]
        return products

    def create_transaction(
        self,
        buyer_sku_code: str,
        customer_no: str,
        ref_id: str,
        testing: bool = False,
    ) -> dict[str, object]:
        self.orders.append((buyer_sku_code, customer_no, ref_id))
        return {
            "ref_id": ref_id,
            "status": "Pending",
            "message": "Transaksi sedang diproses",
            "buyer_sku_code": buyer_sku_code,
            "customer_no": customer_no,
            "price": 6_200,
            "testing": testing,
        }

    def transaction_status(
        self,
        buyer_sku_code: str,
        customer_no: str,
        ref_id: str,
    ) -> dict[str, object]:
        self.status_requests.append((buyer_sku_code, customer_no, ref_id))
        if not self.status_responses:
            raise AssertionError("Unexpected transaction status request")
        return self.status_responses.pop(0)

class FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, *args) -> bool:
        return False

class FakeHermesStatus:
    def summary(self) -> str:
        self.calls += 1
        return 'Status Hermes' + os.linesep + 'Kartu aktif: 1'

    def __init__(self) -> None:
        self.calls = 0

class FakeLiveHermesStatus:
    def __init__(self) -> None:
        self.calls = 0
        self.values = ['Status A', 'Status A', 'Status B']

    def summary(self) -> str:
        value = self.values[min(self.calls, len(self.values) - 1)]
        self.calls += 1
        return value

class FakeHermesChat:
    def __init__(self) -> None:
        self.questions: list[str] = []
        self.release = threading.Event()

    def ask(self, question: str) -> str:
        self.questions.append(question)
        self.release.wait(timeout=2)
        return 'Jawaban Hermes'


class TelegramStoreTests(unittest.TestCase):
    def test_digiflazz_client_uses_required_buyer_signatures(self) -> None:
        transport = FakeTransport(
            {
                ("POST", "https://api.digiflazz.com/v1/price-list"): {"data": []},
                ("POST", "https://api.digiflazz.com/v1/transaction"): {
                    "data": {"ref_id": "INV-1", "status": "Pending"}
                },
            }
        )
        client = DigiflazzClient(username="store-user", api_key="api-key", transport=transport)

        client.price_list()
        client.create_transaction("BRIZZI5", "08123456789", "INV-1")

        self.assertEqual(transport.calls[0][2]["cmd"], "price")
        self.assertEqual(transport.calls[1][2]["buyer_sku_code"], "BRIZZI5")
        self.assertEqual(transport.calls[1][2]["customer_no"], "08123456789")
        self.assertEqual(transport.calls[1][2]["ref_id"], "INV-1")

    def test_digiflazz_client_creates_deposit_ticket(self) -> None:
        transport = FakeTransport(
            {
                ("POST", "https://api.digiflazz.com/v1/deposit"): {
                    "data": {
                        "rc": "00",
                        "bank": "BCA",
                        "payment_method": "Bank Transfer",
                        "account_no": "0123 4567 89",
                        "amount": 200001,
                        "notes": "A6R5UPV",
                    }
                }
            }
        )
        client = DigiflazzClient(username="store-user", api_key="api-key", transport=transport)

        result = client.create_deposit(200_000, "BCA", "Haidi")

        self.assertEqual(transport.calls[0][0], "POST")
        self.assertEqual(transport.calls[0][1], "https://api.digiflazz.com/v1/deposit")
        self.assertEqual(transport.calls[0][2]["amount"], 200_000)
        self.assertEqual(transport.calls[0][2]["bank"], "BCA")
        self.assertEqual(transport.calls[0][2]["owner_name"], "Haidi")
        self.assertEqual(result["notes"], "A6R5UPV")

    def test_digiflazz_client_switches_sandbox_and_production_keys(self) -> None:
        transport = FakeTransport(
            {
                ("POST", "https://api.digiflazz.com/v1/transaction"): {
                    "data": {"ref_id": "r1", "status": "Sukses"}
                }
            }
        )
        client = DigiflazzClient(
            username="store-user",
            api_key="production-key",
            transport=transport,
            development_key="development-key",
        )

        client.set_mode("sandbox")
        client.create_transaction("xld10", "087800001230", "sandbox-ref", testing=True)
        self.assertEqual(client.api_key, "development-key")
        self.assertEqual(transport.calls[0][2]["sign"], client._sign("sandbox-ref"))

        client.set_mode("prod")
        client.create_transaction("xld10", "087800001230", "prod-ref")
        self.assertEqual(client.api_key, "production-key")
        self.assertEqual(transport.calls[1][2]["sign"], client._sign("prod-ref"))

    def test_saldo_menu_shows_balance_and_deposit_nominals(self) -> None:
        service = TelegramStoreService(FakeDigiflazz())
        sent: list[tuple[int, str, dict[str, object] | None]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text, reply_markup)),
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/saldo"}})

        self.assertIn("<b>Isi Saldo</b>", sent[0][1])
        self.assertIn("Saldo saat ini: <code>Rp 250.000</code>", sent[0][1])
        self.assertIn("Rp 200.000", sent[0][1])
        reply_markup = next(item[2] for item in sent if item[2] is not None) or {}
        texts = [row["text"] for item in reply_markup.get("inline_keyboard", []) for row in item]
        self.assertIn("Rp 200.000", texts)

    def test_saldo_nominal_prompts_bank_and_owner_name(self) -> None:
        service = TelegramStoreService(FakeDigiflazz())
        sent: list[tuple[int, str, dict[str, object] | None]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text, reply_markup)),
            answer_callback_query=lambda callback_query_id: None,
        )

        bot.handle_update(
            {"callback_query": {"id": "cb-1", "data": "/isidaldo 200000", "message": {"chat": {"id": 101}}}}
        )

        self.assertIn("<b>Pilih Bank</b>", sent[0][1])
        markup = next(item[2] for item in sent if item[2] is not None) or {}
        buttons = [button["text"] for row in markup.get("inline_keyboard", []) for button in row]
        self.assertEqual(["BCA", "MANDIRI", "BRI", "BNI", "Flip", "ShopeePay"], buttons)
        callbacks = [button["callback_data"] for row in markup.get("inline_keyboard", []) for button in row]
        self.assertEqual(['/bank 200000 BCA', '/bank 200000 MANDIRI', '/bank 200000 BRI', '/bank 200000 BNI', '/bank 200000 Flip', '/bank 200000 ShopeePay'], callbacks)

    def test_bank_selection_prompts_owner_name(self) -> None:
        service = TelegramStoreService(FakeDigiflazz())
        sent: list[tuple[int, str]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
            answer_callback_query=lambda callback_query_id: None,
        )

        bot.handle_update(
            {"callback_query": {"id": "cb-1", "data": "/isidaldo 200000", "message": {"chat": {"id": 101}}}}
        )

        self.assertIn("<b>Pilih Bank</b>", sent[0][1])

        bot.handle_update(
            {"callback_query": {"id": "cb-2", "data": "/bank 200000 BCA", "message": {"chat": {"id": 101}}}}
        )

        self.assertIn("<b>Deposit Rp 200.000</b>", sent[1][1])
        self.assertIn("Kirim nama pemilik rekening.", sent[1][1])

    def test_sandbox_bank_selection_shows_only_supported_banks(self) -> None:
        service = TelegramStoreService(FakeDigiflazz())
        sent: list[tuple[int, str, dict[str, object] | None]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text, reply_markup)),
            answer_callback_query=lambda callback_query_id: None,
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/sandbox"}})
        bot.handle_update(
            {"callback_query": {"id": "cb-1", "data": "/isidaldo 200000", "message": {"chat": {"id": 101}}}}
        )

        markup = sent[1][2] or {}
        buttons = [button["text"] for row in markup.get("inline_keyboard", []) for button in row]
        self.assertEqual(["Flip", "ShopeePay"], buttons)

    def test_bank_selection_stores_amount_and_accepts_owner_name(self) -> None:
        service = TelegramStoreService(FakeDigiflazz())
        sent: list[tuple[int, str]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
            answer_callback_query=lambda callback_query_id: None,
        )

        bot.handle_update(
            {"callback_query": {"id": "cb-1", "data": "/bank 200000 BCA", "message": {"chat": {"id": 101}}}}
        )
        bot.handle_update({"message": {"chat": {"id": 101}, "text": "Haidi"}})

        self.assertEqual((200_000, "BCA", "Haidi"), service.digiflazz.deposit_request)
        self.assertIn("<b>Tiket Deposit Dibuat</b>", sent[1][1])

    def test_saldo_shows_manual_nominal_choice(self) -> None:
        service = TelegramStoreService(FakeDigiflazz())
        sent: list[tuple[int, str, dict[str, object] | None]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text, reply_markup)),
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/saldo"}})

        buttons = [
            button
            for row in (sent[0][2] or {}).get("inline_keyboard", [])
            for button in row
        ]
        self.assertIn({"text": "Input Nominal", "callback_data": "/nominal"}, buttons)

    def test_manual_nominal_uses_guided_numeric_input(self) -> None:
        service = TelegramStoreService(FakeDigiflazz())
        sent: list[tuple[int, str, dict[str, object] | None]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text, reply_markup)),
            answer_callback_query=lambda callback_query_id: None,
        )

        bot.handle_update({"callback_query": {"id": "cb-1", "data": "/nominal", "message": {"chat": {"id": 101}}}})
        bot.handle_update({"message": {"chat": {"id": 101}, "text": "300000"}})

        self.assertIn("Kirim nominal deposit.", sent[0][1])
        self.assertIn("<b>Pilih Bank</b>", sent[1][1])
        markup = sent[1][2] or {}
        buttons = [button["text"] for row in markup.get("inline_keyboard", []) for button in row]
        self.assertIn("Flip", buttons)

    def test_bank_selection_uses_configured_owner_name_automatically(self) -> None:
        service = TelegramStoreService(FakeDigiflazz())
        sent: list[tuple[int, str]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            deposit_owner_name="Haidi",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
            answer_callback_query=lambda callback_query_id: None,
        )

        bot.handle_update(
            {"callback_query": {"id": "cb-1", "data": "/bank 200000 BCA", "message": {"chat": {"id": 101}}}}
        )

        self.assertEqual((200_000, "BCA", "Haidi"), service.digiflazz.deposit_request)
        self.assertIn("<b>Tiket Deposit Dibuat</b>", sent[0][1])

    def test_deposit_ticket_normalizes_account_number_for_copy(self) -> None:
        service = TelegramStoreService(FakeDigiflazz())
        sent: list[tuple[int, str]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
            answer_callback_query=lambda callback_query_id: None,
        )

        bot.handle_update(
            {"message": {"chat": {"id": 101}, "text": "/isidaldo 200000 BCA Haidi"}}
        )

        self.assertIn("<code>0123456789</code>", sent[0][1])
        self.assertNotIn("<code>0123 4567 89</code>", sent[0][1])

    def test_digiflazz_client_checks_transaction_status(self) -> None:
        transport = FakeTransport(
            {
                ("POST", "https://api.digiflazz.com/v1/transaction"): {
                    "data": {"ref_id": "invoice-1", "status": "Sukses", "rc": "00"}
                }
            }
        )
        client = DigiflazzClient(username="store-user", api_key="api-key", transport=transport)

        result = client.transaction_status("SKU1", "08123456789", "invoice-1")

        self.assertEqual(transport.calls[0][2]["cmd"], "status")
        self.assertEqual(transport.calls[0][2]["buyer_sku_code"], "SKU1")
        self.assertEqual(transport.calls[0][2]["customer_no"], "08123456789")
        self.assertEqual(transport.calls[0][2]["ref_id"], "invoice-1")
        self.assertEqual(result["status"], "Sukses")

    def test_cekstatus_refreshes_pending_order_from_digiflazz(self) -> None:
        digiflazz = FakeDigiflazz()
        service = TelegramStoreService(digiflazz)
        order = service.order("BRIZZI5", "08123456789")
        service.orders.save({**order, "status": "Pending"})
        digiflazz.status_responses.append(
            {"ref_id": order["invoice"], "status": "Sukses", "rc": "00", "message": "Transaksi sukses"}
        )

        refreshed = service.status(order["invoice"])

        self.assertEqual(digiflazz.status_requests[0], ("BRIZZI5", "08123456789", order["invoice"]))
        self.assertEqual(refreshed["status"], "Sukses")
        self.assertEqual(service.orders.find(order["invoice"])["status"], "Sukses")

    def test_product_number_selects_product_and_prompts_customer_number(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[tuple[int, str]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/produk"}})
        bot.handle_update({"message": {"chat": {"id": 101}, "text": "1"}})

        self.assertIn("Produk dipilih: <b>Token PLN 100</b>", sent[-1][1])
        self.assertIn("Harga: <code>Rp 14.041</code>", sent[-1][1])
        self.assertIn("Kirim nomor tujuan sekarang.", sent[-1][1])

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "081234554320"}})
        self.assertIn("Pesanan Dibuat", sent[-1][1])

    def test_product_list_shows_sorted_inline_buttons(self) -> None:
        class CatalogDigiflazz:
            def price_list(self, code: str | None = None) -> list[dict[str, object]]:
                products = [
                    {
                        "buyer_sku_code": "OTHER1",
                        "product_name": "Produk Lain",
                        "category": "Games",
                        "brand": "OTHER",
                        "price": 10_000,
                        "buyer_product_status": True,
                        "seller_product_status": True,
                    },
                    {
                        "buyer_sku_code": "tsel10",
                        "product_name": "Telkomsel 10.000",
                        "category": "Pulsa",
                        "brand": "TELKOMSEL",
                        "price": 10_800,
                        "buyer_product_status": True,
                        "seller_product_status": True,
                    },
                    {
                        "buyer_sku_code": "pdam20",
                        "product_name": "PDAM 20.000",
                        "category": "PDAM",
                        "brand": "PDAM",
                        "price": 20_000,
                        "buyer_product_status": True,
                        "seller_product_status": True,
                    },
                    {
                        "buyer_sku_code": "pln20",
                        "product_name": "PLN 20.000",
                        "category": "PLN",
                        "brand": "PLN",
                        "price": 21_000,
                        "buyer_product_status": True,
                        "seller_product_status": True,
                    },
                ]
                if code:
                    return [item for item in products if item["buyer_sku_code"] == code]
                return products

        service = TelegramStoreService(CatalogDigiflazz())
        sent: list[tuple[int, str, dict[str, object] | None]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text, reply_markup)),
            answer_callback_query=lambda callback_query_id: None,
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/produk"}})

        markup = next(item[2] for item in sent if item[2] is not None)
        self.assertIsNotNone(markup)
        callbacks = [
            button["callback_data"]
            for rows in markup["inline_keyboard"]
            for button in rows
        ]
        self.assertEqual(callbacks, ["/pilih pln20", "/pilih pdam20", "/pilih tsel10", "/pilih OTHER1"])

    def test_selected_product_accepts_manual_customer_number(self) -> None:
        service = TelegramStoreService(FakeDigiflazz())
        sent: list[tuple[int, str]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
            answer_callback_query=lambda callback_query_id: None,
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/pilih BRIZZI5"}})
        bot.handle_update({"message": {"chat": {"id": 101}, "text": "08123456789"}})

        self.assertIn("Produk dipilih: <b>Brizzi 5</b>", sent[0][1])
        self.assertIn("Kirim nomor tujuan", sent[0][1])
        self.assertIn("Pesanan Dibuat", sent[-1][1])
        self.assertEqual(service.digiflazz.orders[0][0], "BRIZZI5")
        self.assertEqual(service.digiflazz.orders[0][1], "08123456789")

    def test_product_selection_to_successful_payment_status_flow(self) -> None:
        digiflazz = FakeDigiflazz(balance=1_000_000)
        orders = InMemoryOrderStore()
        service = TelegramStoreService(digiflazz, orders=orders)
        sent: list[tuple[int, str]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
            answer_callback_query=lambda callback_query_id: None,
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/produk"}})
        bot.handle_update({"message": {"chat": {"id": 101}, "text": "2"}})
        bot.handle_update({"message": {"chat": {"id": 101}, "text": "081234554320"}})

        self.assertIn("Pesanan Dibuat", sent[-1][1])
        order_message = sent[-1][1]
        invoice = order_message.split("Invoice: <code>")[-1].split("</code>")[0] if "Invoice: <code>" in order_message else order_message.split("Invoice: ")[-1].splitlines()[0]
        self.assertEqual("BRIZZI5", digiflazz.orders[0][0])
        self.assertEqual("081234554320", digiflazz.orders[0][1])

        digiflazz.status_responses.append(
            {
                "ref_id": invoice,
                "status": "Sukses",
                "rc": "00",
                "message": "Transaksi sukses",
                "price": 11_500,
            }
        )
        bot.handle_update({"message": {"chat": {"id": 101}, "text": f"/cekstatus {invoice}"}})

        self.assertIn("Invoice:", sent[-1][1])
        self.assertIn("Status: <b>Sukses</b>", sent[-1][1])
        self.assertEqual("Sukses", orders.find(invoice)["status"])
        self.assertEqual(1, len(orders.ledger_entries(invoice)))
        self.assertLess(orders.ledger_entries(invoice)[0]["amount"], 0)

    def test_product_selection_to_failed_payment_status_flow(self) -> None:
        digiflazz = FakeDigiflazz(balance=1_000_000)
        orders = InMemoryOrderStore()
        service = TelegramStoreService(digiflazz, orders=orders)
        sent: list[tuple[int, str]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
            answer_callback_query=lambda callback_query_id: None,
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/produk"}})
        bot.handle_update({"message": {"chat": {"id": 101}, "text": "2"}})
        bot.handle_update({"message": {"chat": {"id": 101}, "text": "081234554320"}})
        order_message = sent[-1][1]
        invoice = order_message.split("Invoice: <code>")[-1].split("</code>")[0] if "Invoice: <code>" in order_message else order_message.split("Invoice: ")[-1].splitlines()[0]

        digiflazz.status_responses.append(
            {"ref_id": invoice, "status": "Gagal", "rc": "X", "message": "Transaksi gagal", "price": 11_500}
        )
        bot.handle_update({"message": {"chat": {"id": 101}, "text": f"/cekstatus {invoice}"}})

        self.assertIn("Status: <b>Gagal</b>", sent[-1][1])
        self.assertEqual("Gagal", orders.find(invoice)["status"])
        self.assertGreater(orders.ledger_entries(invoice)[0]["amount"], 0)

    def test_product_list_excludes_free_fire(self) -> None:
        class CatalogDigiflazz:
            def price_list(self, code: str | None = None) -> list[dict[str, object]]:
                products = [
                    {
                        "buyer_sku_code": "ff50",
                        "product_name": "Free Fire 50 Diamond",
                        "category": "Games",
                        "brand": "FREE FIRE",
                        "price": 5_880,
                        "buyer_product_status": True,
                        "seller_product_status": True,
                    },
                    {
                        "buyer_sku_code": "s10",
                        "product_name": "Telkomsel 10.000",
                        "category": "Pulsa",
                        "brand": "TELKOMSEL",
                        "price": 10_823,
                        "buyer_product_status": True,
                        "seller_product_status": True,
                    },
                ]
                if code:
                    return [item for item in products if item["buyer_sku_code"] == code]
                return products

        service = TelegramStoreService(CatalogDigiflazz())
        sent: list[tuple[int, str, dict[str, object] | None]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text, reply_markup)),
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/produk"}})

        self.assertNotIn("Free Fire 50 Diamond", sent[0][1])
        markup = next(item[2] for item in sent if item[2] is not None) or {}
        texts = [button["text"] for rows in markup.get("inline_keyboard", []) for button in rows]
        self.assertNotIn("Free Fire 50 Diamond", texts)
        self.assertIn("Telkomsel 10.000", texts)

    def test_product_list_shows_only_telkomsel_mobile_products(self) -> None:
        class CatalogDigiflazz:
            def price_list(self, code: str | None = None) -> list[dict[str, object]]:
                products = [
                    {
                        "buyer_sku_code": "ax10",
                        "product_name": "Axis 10.000",
                        "category": "Pulsa",
                        "brand": "AXIS",
                        "price": 10_992,
                        "buyer_product_status": True,
                        "seller_product_status": True,
                    },
                    {
                        "buyer_sku_code": "s10",
                        "product_name": "Telkomsel 10.000",
                        "category": "Pulsa",
                        "brand": "TELKOMSEL",
                        "price": 10_823,
                        "buyer_product_status": True,
                        "seller_product_status": True,
                    },
                    {
                        "buyer_sku_code": "pln20",
                        "product_name": "PLN 20.000",
                        "category": "PLN",
                        "brand": "PLN",
                        "price": 21_260,
                        "buyer_product_status": True,
                        "seller_product_status": True,
                    },
                    {
                        "buyer_sku_code": "pdam20",
                        "product_name": "PDAM 20.000",
                        "category": "PDAM",
                        "brand": "PDAM",
                        "price": 20_000,
                        "buyer_product_status": True,
                        "seller_product_status": True,
                    },
                ]
                if code:
                    return [item for item in products if item["buyer_sku_code"] == code]
                return products

        service = TelegramStoreService(CatalogDigiflazz())
        sent: list[tuple[int, str, dict[str, object] | None]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text, reply_markup)),
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/produk"}})

        self.assertNotIn("Axis 10.000", sent[0][1])
        markup = next(item[2] for item in sent if item[2] is not None) or {}
        texts = [button["text"] for rows in markup.get("inline_keyboard", []) for button in rows]
        self.assertNotIn("Axis 10.000", texts)

    def test_product_list_blocks_mobile_providers_even_with_unknown_category(self) -> None:
        class CatalogDigiflazz:
            def price_list(self, code: str | None = None) -> list[dict[str, object]]:
                return [
                    {
                        "buyer_sku_code": "xld10",
                        "product_name": "XL Data 10.000",
                        "category": "Paket Data Baru",
                        "brand": "XL",
                        "price": 10_000,
                        "buyer_product_status": True,
                        "seller_product_status": True,
                    },
                    {
                        "buyer_sku_code": "tsel10",
                        "product_name": "Telkomsel 10.000",
                        "category": "Pulsa",
                        "brand": "TELKOMSEL",
                        "price": 10_800,
                        "buyer_product_status": True,
                        "seller_product_status": True,
                    },
                ]

        service = TelegramStoreService(CatalogDigiflazz())
        products = service.list_products()

        self.assertEqual([item["buyer_sku_code"] for item in products], ["tsel10"])

    def test_bot_defaults_to_production_mode(self) -> None:
        service = TelegramStoreService(FakeDigiflazz())
        bot = TelegramStoreBot(token="token", service=service)

        self.assertEqual(bot.mode, "prod")
        self.assertEqual(service.testing, False)
        self.assertIn("Mode: <b>Production</b>", format_deposit_menu(service.digiflazz.balance()))

    def test_bot_switches_to_sandbox_and_back_to_production(self) -> None:
        service = TelegramStoreService(FakeDigiflazz())
        bot = TelegramStoreBot(
            token="token",
            service=service,
            send_message=lambda chat_id, text, reply_markup=None: None,
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/sandbox"}})

        self.assertEqual(bot.mode, "sandbox")
        self.assertEqual(service.testing, True)

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/prod"}})

        self.assertEqual(bot.mode, "prod")
        self.assertEqual(service.testing, False)

    def test_sandbox_purchase_uses_testing_flag(self) -> None:
        service = TelegramStoreService(FakeDigiflazz())
        sent: list[tuple[int, str]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/sandbox"}})
        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/beli BRIZZI5 08123456789"}})

        self.assertEqual(service.digiflazz.orders[0][0], "BRIZZI5")

    def test_store_lists_products_with_markup_and_orders_as_buyer(self) -> None:
        digiflazz = FakeDigiflazz()
        orders = InMemoryOrderStore()
        service = TelegramStoreService(digiflazz, markup_percent=10, orders=orders)

        products = service.list_products("PLN")
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]["sale_price"], 14_041)

        order = service.order("BRIZZI5", "08123456789")
        self.assertTrue(order["invoice"].startswith("HN-"))
        self.assertEqual(order["status"], "Pending")
        self.assertEqual(digiflazz.orders[0][0], "BRIZZI5")
        self.assertEqual(digiflazz.orders[0][1], "08123456789")

    def test_order_requires_positive_digiflazz_balance(self) -> None:
        digiflazz = FakeDigiflazz(balance=0)
        service = TelegramStoreService(digiflazz)

        with self.assertRaisesRegex(ValueError, "Isi saldo dulu"):
            service.order("BRIZZI5", "08123456789")

        self.assertEqual(digiflazz.orders, [])

    def test_order_rejects_insufficient_digiflazz_balance(self) -> None:
        digiflazz = FakeDigiflazz(balance=6_199)
        service = TelegramStoreService(digiflazz)

        with self.assertRaisesRegex(ValueError, "Saldo tidak cukup"):
            service.order("BRIZZI5", "08123456789")

        self.assertEqual(digiflazz.orders, [])

    def test_bot_replies_with_store_commands(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[tuple[int, str]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/start"}})
        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/produk BRIZZI"}})
        purchase = service.order("BRIZZI5", "08123456789")
        bot.handle_update(
            {"message": {"chat": {"id": 101}, "text": f"/status {purchase['invoice']}"}}
        )

        self.assertIn("@hn_assistent_bot", sent[0][1])
        self.assertIn("Brizzi 5", sent[2][1])
        self.assertIn("Rp 7.570", sent[2][1])
        self.assertIn(purchase["invoice"], sent[-1][1])

    def test_bot_accepts_product_alias(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[tuple[int, str]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/product BRIZZI"}})

        self.assertIn("Brizzi 5", sent[-1][1])

    def test_product_list_uses_scannable_catalog_layout(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[tuple[int, str]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/produk"}})

        expected = (
            "<b>Daftar Produk</b>\n\n"
            "1. <b>Brizzi 5</b>\n"
            "   BRIZZI • E-Money\n"
            "   <code>BRIZZI5</code> • Rp 7.570\n\n"
            "2. <b>Token PLN 100</b>\n"
            "   PLN • PLN\n"
            "   <code>PLN100</code> • Rp 14.041\n\n"
            "Pilih berdasarkan nomor produk."
        )
        self.assertEqual(expected, sent[-1][1])

    def test_bot_accepts_indonesian_command_aliases(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[tuple[int, str]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/bantuan"}})
        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/produk BRIZZI"}})
        purchase = service.order("BRIZZI5", "08123456789")
        bot.handle_update(
            {"message": {"chat": {"id": 101}, "text": f"/cekstatus {purchase['invoice']}"}}
        )

        self.assertIn("Selamat datang", sent[0][1])
        self.assertIn("Brizzi 5", sent[2][1])
        self.assertIn(purchase["invoice"], sent[-1][1])

    def test_hermes_status_provider_summarizes_progress_cards(self) -> None:
        calls: list[str] = []

        def trello_fetch(url: str) -> list[dict[str, object]]:
            calls.append(url)
            return [
                {
                    'name': '[P0] Perbaiki stok minus',
                    'shortUrl': 'https://trello.com/c/example',
                    'checklists': [
                        {
                            'name': 'Checklist',
                            'checkItems': [
                                {'name': 'Tambah test', 'state': 'complete'},
                                {'name': 'Perbaiki stok', 'state': 'incomplete'},
                            ],
                        }
                    ],
                }
            ]

        jobs_path = Path(tempfile.gettempdir()) / 'hermes_status_test_jobs.json'
        jobs_path.write_text(
            json.dumps(
                {
                    'jobs': [
                        {
                            'name': 'Trello Todo Worker - Inventory',
                            'enabled': True,
                            'state': 'scheduled',
                            'schedule_display': 'every 1m',
                            'last_status': 'error',
                            'last_error': 'Gateway tidak siap',
                        }
                    ]
                }
            ),
            encoding='utf-8',
        )
        try:
            provider = HermesStatusProvider(
                trello_fetch=trello_fetch,
                trello_key='test-key',
                trello_token='test-token',
                progress_list_id='progress-list',
                jobs_path=jobs_path,
            )
            summary = provider.summary()
        finally:
            jobs_path.unlink(missing_ok=True)

        self.assertEqual(len(calls), 1)
        self.assertIn('/1/lists/progress-list/cards', calls[0])
        self.assertIn('checklists=all', calls[0])
        self.assertIn('key=test-key', calls[0])
        self.assertIn('token=test-token', calls[0])
        self.assertIn('Status Hermes', summary)
        self.assertIn('Trello Todo Worker - Inventory', summary)
        self.assertIn('Status cron: error', summary)
        self.assertIn('Gateway tidak siap', summary)
        self.assertIn('[P0] Perbaiki stok minus', summary)
        self.assertIn('[x] Tambah test', summary)
        self.assertIn('[ ] Perbaiki stok', summary)

    def test_hermes_status_provider_reports_empty_progress(self) -> None:
        provider = HermesStatusProvider(
            trello_fetch=lambda url: [],
            trello_key='test-key',
            trello_token='test-token',
            progress_list_id='progress-list',
            jobs_path=None,
        )

        summary = provider.summary()

        self.assertIn('Tidak ada kartu di progress.', summary)

    def test_hermes_status_provider_handles_fetch_failure(self) -> None:
        def trello_fetch(url: str) -> list[dict[str, object]]:
            raise RuntimeError('Trello tidak bisa dihubungi')

        provider = HermesStatusProvider(
            trello_fetch=trello_fetch,
            trello_key='test-key',
            trello_token='test-token',
            progress_list_id='progress-list',
            jobs_path=None,
        )

        summary = provider.summary()

        self.assertIn('Status Hermes belum tersedia.', summary)
        self.assertIn('Trello tidak bisa dihubungi', summary)

    def test_hermes_status_provider_includes_running_delegation_activity(self) -> None:
        delegation_root = Path(tempfile.gettempdir()) / 'hermes_live_delegation_test'
        delegation_dir = delegation_root / 'deleg_test'
        delegation_dir.mkdir(parents=True, exist_ok=True)
        log_path = delegation_dir / 'task-0.log'
        log_path.write_text(
            os.linesep.join(['14:20:01 tool      | -> terminal(rg DataTable)', '14:20:02 result   | terminal ok']),
            encoding='utf-8',
        )
        (delegation_dir / 'manifest.json').write_text(
            json.dumps(
                {
                    'started': '2026-10-22 14:20:00',
                    'tasks': [
                        {
                            'goal': 'Inventaris semua halaman list MVP',
                            'status': 'running',
                            'log': str(log_path),
                        }
                    ],
                }
            ),
            encoding='utf-8',
        )
        provider = HermesStatusProvider(
            trello_fetch=lambda url: [],
            trello_key='test-key',
            trello_token='test-token',
            progress_list_id='progress-list',
            jobs_path=None,
            delegation_root=delegation_root,
            agent_log_path=delegation_root / 'agent.log',
        )
        agent_log = delegation_root / 'agent.log'
        agent_log.write_text(
            os.linesep.join(
                [
                    '2026-10-22 14:50:01,309 INFO [session] agent.conversation_loop: API call #158: model=cd provider=custom',
                    '2026-10-22 14:50:12,089 INFO [session] agent.tool_executor: tool terminal completed (0.99s, 571 chars)',
                    '2026-10-22 14:50:17,120 INFO agent.codex_runtime: Codex stream first substantive progress',
                ]
            ),
            encoding='utf-8',
        )
        try:
            summary = provider.summary()
        finally:
            log_path.unlink(missing_ok=True)
            (delegation_dir / 'manifest.json').unlink(missing_ok=True)
            (delegation_root / 'agent.log').unlink(missing_ok=True)
            delegation_dir.rmdir()
            delegation_root.rmdir()

        self.assertIn('Aktivitas Hermes', summary)
        self.assertIn('Inventaris semua halaman list MVP', summary)
        self.assertIn('Status: running', summary)
        self.assertIn('Log terakhir:', summary)
        self.assertIn('terminal ok', summary)
        self.assertIn('Proses Hermes', summary)
        self.assertIn('Berpikir: API call #158', summary)
        self.assertIn('Proses: tool terminal completed', summary)
        self.assertIn('Berpikir: Codex stream first substantive progress', summary)

    def test_start_shows_menu_buttons(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[tuple[int, str, dict[str, object] | None]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append(
                (chat_id, text, reply_markup)
            ),
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/start"}})

        markup = next(item[2] for item in sent if item[2] is not None)
        self.assertIsNotNone(markup)
        rows = markup["inline_keyboard"]
        self.assertEqual(len(rows), 5)
        self.assertEqual(len(rows[1]), 2)
        self.assertEqual(len(rows[2]), 1)
        row_texts = {button["text"] for row in rows for button in row}
        self.assertIn("Daftar Produk", row_texts)
        self.assertIn("Beli Produk", row_texts)
        self.assertIn("Cek Status", row_texts)
        self.assertIn("Isi Saldo", row_texts)

    def test_start_omits_hermes_monitoring_buttons(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[tuple[int, str, dict[str, object] | None]] = []
        bot = TelegramStoreBot(
            token='token',
            service=service,
            bot_username='@hn_assistent_bot',
            send_message=lambda chat_id, text, reply_markup=None: sent.append(
                (chat_id, text, reply_markup)
            ),
        )

        bot.handle_update({'message': {'chat': {'id': 101}, 'text': '/start'}})

        markup = next(item[2] for item in sent if item[2] is not None)
        assert markup is not None
        rows = markup['inline_keyboard']
        row_texts = {button['text'] for row in rows for button in row}
        self.assertNotIn('Hermes Live', row_texts)
        self.assertNotIn('Stop Hermes Live', row_texts)
        self.assertNotIn('Daftar Perintah', row_texts)

    def test_perintah_shows_menu_buttons(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[tuple[int, str, dict[str, object] | None]] = []
        bot = TelegramStoreBot(
            token='token',
            service=service,
            bot_username='@hn_assistent_bot',
            send_message=lambda chat_id, text, reply_markup=None: sent.append(
                (chat_id, text, reply_markup)
            ),
        )

        bot.handle_update({'message': {'chat': {'id': 101}, 'text': '/perintah'}})

        markup = next(item[2] for item in sent if item[2] is not None)
        assert markup is not None
        row_texts = {button['text'] for row in markup['inline_keyboard'] for button in row}
        self.assertIn('Daftar Produk', row_texts)
        self.assertNotIn('Status Hermes', row_texts)

    def test_bot_shows_hermes_status(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[tuple[int, str]] = []
        hermes_status = FakeHermesStatus()
        bot = TelegramStoreBot(
            token='token',
            service=service,
            bot_username='@hn_assistent_bot',
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
            hermes_status=hermes_status,
        )

        bot.handle_update({'message': {'chat': {'id': 101}, 'text': '/hermes'}})
        bot.handle_update({'message': {'chat': {'id': 101}, 'text': '/starthermes'}})
        bot.handle_update({'message': {'chat': {'id': 101}, 'text': '/statushermes'}})

        self.assertEqual(hermes_status.calls, 3)
        self.assertTrue(all('Kartu aktif: 1' in text for _, text in sent))

    def test_bot_shows_fallback_when_hermes_status_missing(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[tuple[int, str]] = []
        bot = TelegramStoreBot(
            token='token',
            service=service,
            bot_username='@hn_assistent_bot',
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
        )

        bot.handle_update({'message': {'chat': {'id': 101}, 'text': '/hermes'}})

        self.assertEqual(sent[0][1], 'Status Hermes belum tersedia.')

    def test_bot_sends_hermes_live_updates_on_changes(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[tuple[int, str]] = []
        hermes_status = FakeLiveHermesStatus()
        bot = TelegramStoreBot(
            token='token',
            service=service,
            bot_username='@hn_assistent_bot',
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
            hermes_status=hermes_status,
            live_interval=0.01,
            live_max_updates=3,
            live_duration_seconds=0.05,
        )

        bot.handle_update({'message': {'chat': {'id': 101}, 'text': '/hermeslive'}})
        deadline = time.time() + 2
        while bot._hermes_live and time.time() < deadline:
            time.sleep(0.01)

        self.assertEqual(hermes_status.calls, 3)
        self.assertEqual(sent[0][1], 'Monitoring Hermes live aktif selama 1 menit. Update dikirim saat ada perubahan.')
        self.assertIn('Status A', sent[1][1])
        self.assertIn('Status B', sent[2][1])
        self.assertNotIn(101, bot._hermes_live)

    def test_bot_ends_hermes_live_after_duration(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[tuple[int, str]] = []
        hermes_status = FakeHermesStatus()
        bot = TelegramStoreBot(
            token='token',
            service=service,
            bot_username='@hn_assistent_bot',
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
            hermes_status=hermes_status,
            live_interval=0.01,
            live_duration_seconds=0.05,
        )

        bot.handle_update({'message': {'chat': {'id': 101}, 'text': '/hermeslive'}})
        deadline = time.time() + 2
        while bot._hermes_live and time.time() < deadline:
            time.sleep(0.01)

        self.assertGreaterEqual(hermes_status.calls, 2)
        self.assertNotIn(101, bot._hermes_live)
        self.assertEqual(sent[-1][1], 'Sesi monitoring Hermes 1 menit selesai.')

    def test_bot_stops_hermes_live_monitoring(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[tuple[int, str]] = []
        bot = TelegramStoreBot(
            token='token',
            service=service,
            bot_username='@hn_assistent_bot',
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
            hermes_status=FakeHermesStatus(),
            live_interval=0.01,
        )

        bot.handle_update({'message': {'chat': {'id': 101}, 'text': '/hermeslive'}})
        deadline = time.time() + 2
        while 101 not in bot._hermes_live and time.time() < deadline:
            time.sleep(0.01)
        bot.handle_update({'message': {'chat': {'id': 101}, 'text': '/hermesstop'}})

        self.assertTrue(sent[-1][1].startswith('Monitoring Hermes live dihentikan.'))
        self.assertNotIn(101, bot._hermes_live)

    def test_bot_reports_hermes_live_already_active(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[tuple[int, str]] = []
        bot = TelegramStoreBot(
            token='token',
            service=service,
            bot_username='@hn_assistent_bot',
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
            hermes_status=FakeHermesStatus(),
            live_interval=1,
        )

        bot.handle_update({'message': {'chat': {'id': 101}, 'text': '/hermeslive'}})
        deadline = time.time() + 2
        while 101 not in bot._hermes_live and time.time() < deadline:
            time.sleep(0.01)
        bot.handle_update({'message': {'chat': {'id': 101}, 'text': '/hermeslive'}})
        bot._hermes_live[101].set()

        self.assertIn('Monitoring Hermes live sudah aktif.', [text for _, text in sent])

    def test_bot_shows_fallback_when_hermes_live_missing(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[tuple[int, str]] = []
        bot = TelegramStoreBot(
            token='token',
            service=service,
            bot_username='@hn_assistent_bot',
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
        )

        bot.handle_update({'message': {'chat': {'id': 101}, 'text': '/hermeslive'}})

        self.assertEqual(sent[0][1], 'Status Hermes belum tersedia.')

    def test_hermes_chat_client_builds_safe_one_shot_query(self) -> None:
        calls: list[tuple[list[str], bytes]] = []

        def runner(command: list[str], input_bytes: bytes, timeout: float) -> object:
            calls.append((command, input_bytes))
            return type('Completed', (), {'returncode': 0, 'stdout': 'Jawaban Hermes', 'stderr': ''})()

        status = FakeHermesStatus()
        client = HermesChatClient(
            runner=runner,
            hermes_binary='hermes.exe',
            workdir=Path('D:/projects/klinik-git'),
            status_provider=status,
            timeout=90,
        )

        answer = client.ask('Apa yang sedang dikerjakan?')

        self.assertEqual(answer, 'Jawaban Hermes')
        command, input_bytes = calls[0]
        self.assertEqual(command[0], 'hermes.exe')
        self.assertIn('chat', command)
        self.assertIn('--query-file', command)
        self.assertIn('-', command)
        self.assertNotIn('--toolsets', command)
        self.assertIn('--yolo', command)
        self.assertIn('--run-budget', command)
        self.assertIn('90', command)
        source_index = command.index('--source') + 1
        self.assertEqual(command[source_index], 'oneshot')
        self.assertIn('--in', command)
        self.assertIn(str(Path('D:/projects/klinik-git')), command)
        self.assertIn('Status Hermes', input_bytes.decode('utf-8'))
        self.assertIn('Apa yang sedang dikerjakan?', input_bytes.decode('utf-8'))
        self.assertIn('Setiap kali mulai bekerja', input_bytes.decode('utf-8'))
        self.assertIn('langkah pertama membaca AGENTS.md', input_bytes.decode('utf-8'))
        self.assertIn('Boleh menambah todo Trello', input_bytes.decode('utf-8'))
        self.assertIn('kebutuhan MVP', input_bytes.decode('utf-8'))
        self.assertIn('akses penuh', input_bytes.decode('utf-8'))
        self.assertNotIn('Jangan mengubah file', input_bytes.decode('utf-8'))
        self.assertEqual(status.calls, 1)

    def test_hermes_chat_client_decodes_bytes_and_removes_session_id(self) -> None:
        calls = []

        def runner(command: list[str], input_bytes: bytes, timeout: float) -> object:
            calls.append((command, input_bytes))
            return type(
                'Completed',
                (),
                {
                    'returncode': 0,
                    'stdout': '**Jawaban rapi.**\r\n\r\n- `Status`: 0\r\n- `Cron`: kosong\r\n\r\nsession_id: local-123'.encode('utf-8'),
                    'stderr': ''.encode('utf-8'),
                },
            )()

        client = HermesChatClient(
            runner=runner,
            hermes_binary='hermes.exe',
            workdir=Path('D:/projects/klinik-git'),
            status_provider=None,
            timeout=30,
        )

        answer = client.ask('Halo')

        self.assertEqual(answer, 'Jawaban rapi.\n\n• Status: 0\n• Cron: kosong')
        _, input_bytes = calls[0]
        query = input_bytes.decode('utf-8')
        self.assertIn('Bahasa Indonesia yang baik dan benar', query)
        self.assertIn('poin diawali •', query)
        self.assertIn('tanpa markdown', query)
        self.assertIn('maksimal 5 poin', query)
        self.assertIn('tanpa log mentah', query)

    def test_hermes_chat_client_reports_command_failure(self) -> None:
        def runner(command: list[str], input_bytes: bytes, timeout: float) -> object:
            return type('Completed', (), {'returncode': 1, 'stdout': '', 'stderr': 'gateway gagal'})()

        client = HermesChatClient(
            runner=runner,
            hermes_binary='hermes.exe',
            workdir=Path('D:/projects/klinik-git'),
            status_provider=None,
            timeout=30,
        )

        with self.assertRaisesRegex(RuntimeError, 'gateway gagal'):
            client.ask('Halo')

    def test_hermes_chat_client_falls_back_to_provider_on_gateway_session_error(self) -> None:
        def runner(command: list[str], input_bytes: bytes, timeout: float) -> object:
            raise RuntimeError('Gateway inaccessible: gateway_other_session')

        provider_calls: list[dict[str, object]] = []

        def provider_post(payload: dict[str, object]) -> dict[str, object]:
            provider_calls.append(payload)
            return {
                'output': [
                    {'type': 'reasoning'},
                    {
                        'type': 'message',
                        'content': [{'type': 'output_text', 'text': 'Jawaban langsung Hermes'}],
                    },
                ]
            }

        client = HermesChatClient(
            runner=runner,
            hermes_binary='hermes.exe',
            workdir=Path('D:/projects/klinik-git'),
            status_provider=FakeHermesStatus(),
            timeout=30,
            provider_post=provider_post,
            provider_model='cd',
        )

        answer = client.ask('Apa status Hermes?')

        self.assertEqual(answer, 'Jawaban langsung Hermes')
        self.assertEqual(len(provider_calls), 1)
        self.assertEqual(provider_calls[0]['model'], 'cd')
        self.assertIn('Apa status Hermes?', str(provider_calls[0]['input']))

    def test_hermes_chat_client_uses_fallback_provider_after_primary_fails(self) -> None:
        def runner(command: list[str], input_bytes: bytes, timeout: float) -> object:
            raise RuntimeError('Gateway inaccessible: gateway_other_session')

        def provider_post(payload: dict[str, object]) -> dict[str, object]:
            raise RuntimeError('primary provider mati')

        fallback_payloads: list[dict[str, object]] = []

        def limo_post(payload: dict[str, object]) -> dict[str, object]:
            fallback_payloads.append(payload)
            return {
                'choices': [
                    {'message': {'role': 'assistant', 'content': 'Jawaban fallback Limo'}}
                ]
            }

        fallback_providers = [
            {
                'name': 'limo_router',
                'base_url': 'https://limo.example/v1',
                'api_key': 'limo-key',
                'model': 'kimi-k3',
                'post': limo_post,
            },
        ]
        client = HermesChatClient(
            runner=runner,
            hermes_binary='hermes.exe',
            workdir=Path('D:/projects/klinik-git'),
            status_provider=FakeHermesStatus(),
            timeout=30,
            provider_post=provider_post,
            provider_model='cd',
            fallback_providers=fallback_providers,
        )

        answer = client.ask('Apa status Hermes?')

        self.assertEqual(answer, 'Jawaban fallback Limo')
        self.assertEqual(len(fallback_payloads), 1)
        self.assertEqual(fallback_payloads[0]['model'], 'kimi-k3')
        self.assertIn('Apa status Hermes?', str(fallback_payloads[0]['messages'][0]['content']))

    def test_hermes_chat_client_uses_second_fallback_when_first_fails(self) -> None:
        def runner(command: list[str], input_bytes: bytes, timeout: float) -> object:
            raise RuntimeError('Gateway inaccessible: gateway_other_session')

        def limo_post(payload: dict[str, object]) -> dict[str, object]:
            raise RuntimeError('limo mati')

        def nilovr_post(payload: dict[str, object]) -> dict[str, object]:
            return {
                'choices': [
                    {'message': {'role': 'assistant', 'content': 'Jawaban fallback Nilovr'}}
                ]
            }

        fallback_providers = [
            {
                'name': 'limo_router',
                'base_url': 'https://limo.example/v1',
                'api_key': 'limo-key',
                'model': 'kimi-k3',
                'post': limo_post,
            },
            {
                'name': 'nilovr',
                'base_url': 'https://nilovr.example/v1',
                'api_key': 'nilovr-key',
                'model': 'glm-5.3-flash',
                'post': nilovr_post,
            },
        ]
        client = HermesChatClient(
            runner=runner,
            hermes_binary='hermes.exe',
            workdir=Path('D:/projects/klinik-git'),
            status_provider=None,
            timeout=30,
            fallback_providers=fallback_providers,
        )

        answer = client.ask('Apa status Hermes?')

        self.assertEqual(answer, 'Jawaban fallback Nilovr')

    def test_build_bot_from_env_loads_fallback_providers_from_env(self) -> None:
        env_path = Path(tempfile.gettempdir()) / 'telegram_store_fallback.env'
        env_path.write_text(
            'TELEGRAM_BOT_TOKEN=token-abc\n'
            'LIMO_ROUTER_BASE_URL=https://limo.example/v1\n'
            'LIMO_ROUTER_API_KEY=limo-key\n'
            'LIMO_ROUTER_MODEL=kimi-k3\n'
            'NILOVR_BASE_URL=https://nilovr.example/v1\n'
            'NILOVR_API_KEY=nilovr-key\n'
            'NILOVR_MODEL=glm-5.3-flash\n'
            'NOCTA_BASE_URL=https://nocta.example/v1\n'
            'NOCTA_API_KEY=nocta-key\n',
            encoding='utf-8',
        )
        env_keys = [
            'TELEGRAM_BOT_TOKEN',
            'LIMO_ROUTER_BASE_URL',
            'LIMO_ROUTER_API_KEY',
            'LIMO_ROUTER_MODEL',
            'NILOVR_BASE_URL',
            'NILOVR_API_KEY',
            'NILOVR_MODEL',
            'NOCTA_BASE_URL',
            'NOCTA_API_KEY',
            'NOCTA_MODEL',
            'MAHI_CENTER_BASE_URL',
            'MAHI_CENTER_API_KEY',
            'MAHI_CENTER_MODEL',
            'TIP_ROUTER_BASE_URL',
            'TIP_ROUTER_API_KEY',
            'TIP_ROUTER_MODEL',
            'MAZOV_BASE_URL',
            'MAZOV_API_KEY',
            'MAZOV_MODEL',
        ]
        try:
            for key in env_keys:
                os.environ.pop(key, None)
            bot = build_bot_from_env(env_path=env_path)

            fallback = bot.hermes_chat.fallback_providers
            self.assertEqual(
                [(provider['name'], provider['model']) for provider in fallback],
                [
                    ('limo_router', 'kimi-k3'),
                    ('nilovr', 'glm-5.3-flash'),
                ],
            )
        finally:
            env_path.unlink(missing_ok=True)
            for key in env_keys:
                os.environ.pop(key, None)

    def test_hermes_chat_client_does_not_fallback_for_other_errors(self) -> None:
        def runner(command: list[str], input_bytes: bytes, timeout: float) -> object:
            raise RuntimeError('model gagal')

        client = HermesChatClient(
            runner=runner,
            hermes_binary='hermes.exe',
            workdir=Path('D:/projects/klinik-git'),
            status_provider=None,
            timeout=30,
            provider_post=lambda payload: {'output': []},
            provider_model='cd',
        )

        with self.assertRaisesRegex(RuntimeError, 'model gagal'):
            client.ask('Halo')

    def test_bot_asks_for_question_when_contact_hermes_empty(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[tuple[int, str]] = []
        bot = TelegramStoreBot(
            token='token',
            service=service,
            bot_username='@hn_assistent_bot',
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
            hermes_chat=FakeHermesChat(),
        )

        bot.handle_update({'message': {'chat': {'id': 101}, 'text': '/hubungihermes'}})

        self.assertEqual(sent[0][1], 'Mode komunikasi Hermes aktif. Kirim pesan biasa; gunakan /akhirihermes untuk berhenti.')
        self.assertIn(101, bot._hermes_chat_sessions)

    def test_bot_contacts_hermes_asynchronously(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[tuple[int, str]] = []
        hermes_chat = FakeHermesChat()
        bot = TelegramStoreBot(
            token='token',
            service=service,
            bot_username='@hn_assistent_bot',
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
            hermes_chat=hermes_chat,
        )

        bot.handle_update(
            {'message': {'chat': {'id': 101}, 'text': '/hubungihermes Apa status todo?'}}
        )
        deadline = time.time() + 2
        while len(sent) < 2 and time.time() < deadline:
            time.sleep(0.01)
        hermes_chat.release.set()
        deadline = time.time() + 2
        while len(sent) < 3 and time.time() < deadline:
            time.sleep(0.01)

        self.assertEqual(hermes_chat.questions, ['Apa status todo?'])
        self.assertEqual(sent[0][1], 'Menghubungi Hermes...')
        self.assertEqual(sent[-1][1], 'Jawaban Hermes')
        self.assertNotIn(101, bot._hermes_chat_busy)

    def test_bot_queues_latest_hermes_question_while_busy(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[tuple[int, str]] = []
        hermes_chat = FakeHermesChat()
        bot = TelegramStoreBot(
            token='token',
            service=service,
            bot_username='@hn_assistent_bot',
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
            hermes_chat=hermes_chat,
        )

        bot.handle_update(
            {'message': {'chat': {'id': 101}, 'text': '/hubungihermes Pertanyaan pertama'}}
        )
        deadline = time.time() + 2
        while 101 not in bot._hermes_chat_busy and time.time() < deadline:
            time.sleep(0.01)
        bot.handle_update(
            {'message': {'chat': {'id': 101}, 'text': '/hubungihermes Pertanyaan kedua'}}
        )
        bot.handle_update(
            {'message': {'chat': {'id': 101}, 'text': 'Pertanyaan ketiga'}}
        )
        hermes_chat.release.set()
        deadline = time.time() + 2
        while len(hermes_chat.questions) < 2 and time.time() < deadline:
            time.sleep(0.01)
        hermes_chat.release.set()
        deadline = time.time() + 2
        while len(sent) < 5 and time.time() < deadline:
            time.sleep(0.01)

        self.assertEqual(hermes_chat.questions, ['Pertanyaan pertama', 'Pertanyaan ketiga'])
        self.assertIn('Hermes sedang menjawab pertanyaan sebelumnya. Pesan ini akan dikirim setelah selesai.', [text for _, text in sent])
        self.assertNotIn(101, bot._hermes_chat_busy)

    def test_callback_query_triggers_command(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[tuple[int, str]] = []
        answered: list[str] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
            answer_callback_query=lambda query_id: answered.append(query_id),
        )

        bot.handle_update(
            {
                "callback_query": {
                    "id": "cb-1",
                    "data": "/produk",
                    "message": {"chat": {"id": 101}},
                }
            }
        )

        self.assertIn("Brizzi 5", sent[-1][1])
        self.assertEqual(answered, ["cb-1"])

    def test_bot_commands_exclude_hermes_status(self) -> None:
        commands = {item['command'] for item in BOT_COMMANDS}

        self.assertNotIn('hermes', commands)
        self.assertNotIn('hermeslive', commands)
        self.assertNotIn('hermesstop', commands)
        self.assertNotIn('hubungihermes', commands)
        self.assertNotIn('akhirihermes', commands)

    def test_help_command_shows_menu(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent = []
        bot = TelegramStoreBot(
            token='token',
            service=service,
            bot_username='@hn_assistent_bot',
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text, reply_markup)),
        )

        bot.handle_update({'message': {'chat': {'id': 101}, 'text': '/help'}})

        self.assertEqual(sent[0][1], 'Selamat datang di @hn_assistent_bot. Silakan pilih menu:')
        self.assertIn('inline_keyboard', sent[0][2])

    def test_set_my_commands_registers_indonesian_menu(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text: None,
        )

        with patch("modules.telegram_store.bot.urllib.request.urlopen") as fake_urlopen:
            fake_urlopen.return_value = FakeResponse(b'{"ok": true}')
            bot.set_my_commands()

        request = fake_urlopen.call_args[0][0]
        self.assertIn("/setMyCommands", request.full_url)
        self.assertIn(b'"produk"', request.data)
        self.assertIn(b'Daftar produk', request.data)
        self.assertIn(b'"saldo"', request.data)

    def test_bot_commands_match_menu_keyboard(self) -> None:
        command_texts = {callback['callback_data'] for row in MENU_KEYBOARD['inline_keyboard'] for callback in row}
        registered = {f"/{item['command']}" for item in BOT_COMMANDS}

        self.assertTrue(registered.issuperset(command_texts))
        self.assertNotIn('/perintah', command_texts)

    def test_menu_omits_hermes_entries(self) -> None:
        command_texts = {callback['callback_data'] for row in MENU_KEYBOARD['inline_keyboard'] for callback in row}
        registered = {f"/{item['command']}" for item in BOT_COMMANDS}

        self.assertFalse(any('hermes' in command for command in command_texts))
        self.assertFalse(any('hermes' in command for command in registered))
        self.assertFalse(any('Hermes' in row['text'] for item in MENU_KEYBOARD['inline_keyboard'] for row in item))

    def test_menu_uses_daftar_produk_label(self) -> None:
        row_texts = {
            row['text']
            for item in MENU_KEYBOARD['inline_keyboard']
            for row in item
        }

        self.assertIn('Daftar Produk', row_texts)
        self.assertNotIn('Lihat Produk', row_texts)

    def test_every_menu_button_triggers_working_command(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[tuple[int, str]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            deposit_owner_name="Haidi",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
            answer_callback_query=lambda callback_query_id: None,
        )
        expectations = {
            "/start": "Selamat datang di @hn_assistent_bot",
            "/produk": "<b>Daftar Produk</b>",
            "/beli": "Format: /beli <SKU> <nomor/id tujuan>",
            "/cekstatus": "Format: /status <invoice>",
            "/saldo": "<b>Isi Saldo</b>",
            "/mode": "<b>Mode Transaksi</b>",
            "/prod": "<b>Mode Production aktif.</b>",
            "/sandbox": "<b>Mode Sandbox aktif.</b>",
        }

        menu_commands = [
            callback["callback_data"]
            for row in MENU_KEYBOARD["inline_keyboard"]
            for callback in row
        ]
        self.assertEqual(list(expectations), menu_commands)

        for command, expected in expectations.items():
            with self.subTest(command=command):
                sent.clear()
                bot.handle_update(
                    {"callback_query": {"id": f"cb-{command}", "data": command, "message": {"chat": {"id": 101}}}}
                )

                self.assertTrue(sent, f"Menu tidak mengirim balasan: {command}")
                self.assertIn(expected, sent[-1][1])
                self.assertNotIn("Perintah tidak dikenal", sent[0][1])

    def test_run_registers_commands_before_polling(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text: None,
        )
        calls: list[str] = []
        bot.set_my_commands = lambda: calls.append("commands")

        def stop_polling(offset: int = 0) -> list[dict[str, object]]:
            raise KeyboardInterrupt

        bot.get_updates = stop_polling
        bot.run()

        self.assertEqual(calls, ["commands"])

    def test_run_continues_after_failed_update_delivery(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[str] = []
        replies: list[str] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: None,
            answer_callback_query=lambda callback_query_id: None,
        )
        bot.set_my_commands = lambda: None
        bot.send_message = (
            lambda chat_id, text, reply_markup=None: replies.append(text)
            if chat_id != 999
            else (_ for _ in ()).throw(
                urllib.error.HTTPError("", 400, "Bad Request", {}, FakeResponse(b'{"ok":false}'))
            )
        )
        updates = [
            {"update_id": 1, "message": {"chat": {"id": 999}, "text": "/cekstatus"}},
            {"update_id": 2, "message": {"chat": {"id": 101}, "text": "/produk"}},
        ]
        responses = list([updates, KeyboardInterrupt()])

        def polling(offset: int = 0) -> list[dict[str, object]]:
            value = responses.pop(0)
            if isinstance(value, BaseException):
                raise value
            return value

        bot.get_updates = polling
        bot.run()

        self.assertIn("<b>Daftar Produk</b>", replies[-1])

    def test_run_continues_after_get_updates_recoverable_failure(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        replies: list[str] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: replies.append(text),
            answer_callback_query=lambda callback_query_id: None,
        )
        bot.set_my_commands = lambda: None
        responses: list[object] = [
            RuntimeError("getUpdates temporarily failed"),
            [{"update_id": 1, "message": {"chat": {"id": 101}, "text": "/produk"}}],
            KeyboardInterrupt(),
        ]

        def polling(offset: int = 0) -> list[dict[str, object]]:
            value = responses.pop(0)
            if isinstance(value, BaseException):
                raise value
            return value

        bot.get_updates = polling
        bot.run()

        self.assertIn("<b>Daftar Produk</b>", replies[-1])

    def test_command_setup_failure_does_not_stop_polling(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        replies: list[str] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: replies.append(text),
            answer_callback_query=lambda callback_query_id: None,
        )
        commands_attempts = 0

        def failing_commands() -> None:
            nonlocal commands_attempts
            commands_attempts += 1
            raise RuntimeError("Telegram command setup failed")

        bot.set_my_commands = failing_commands

        responses = [[{"update_id": 1, "message": {"chat": {"id": 101}, "text": "/health"}}], KeyboardInterrupt()]

        def polling(offset: int = 0) -> list[dict[str, object]]:
            value = responses.pop(0)
            if isinstance(value, BaseException):
                raise value
            return value

        bot.get_updates = polling

        bot.run()

        self.assertEqual(1, commands_attempts)
        self.assertIn("<b>Status Bot</b>", replies[0])

    def test_offset_store_failure_does_not_stop_polling(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        replies: list[str] = []
        set_calls = 0

        class FailingStateStore:
            def get_update_offset(self) -> int:
                return 0

            def set_update_offset(self, value: int) -> None:
                nonlocal set_calls
                set_calls += 1
                raise RuntimeError("state db locked")

        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: replies.append(text),
            answer_callback_query=lambda callback_query_id: None,
            update_offset_store=FailingStateStore(),
        )
        bot.set_my_commands = lambda: None

        def polling(offset: int = 0) -> list[dict[str, object]]:
            if set_calls == 0:
                return [{"update_id": 1, "message": {"chat": {"id": 101}, "text": "/produk"}}]
            raise KeyboardInterrupt()

        bot.get_updates = polling
        bot.run()

        self.assertEqual(1, set_calls)
        self.assertIn("<b>Daftar Produk</b>", replies[-1])

    def test_unexpected_fatal_polling_failure_restarts_loop(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        replies: list[str] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: replies.append(text),
            answer_callback_query=lambda callback_query_id: None,
        )
        bot.set_my_commands = lambda: None
        calls = {"count": 0}

        def polling(offset: int = 0) -> list[dict[str, object]]:
            calls["count"] += 1
            if calls["count"] == 1:
                raise SystemExit("temporary fatal polling failure")
            raise KeyboardInterrupt()

        bot.get_updates = polling
        bot.run()

        self.assertEqual(2, calls["count"])
        self.assertEqual([], replies)

    def test_polling_offset_is_restored_and_saved_from_state_store(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        offsets: list[int] = []
        seen_offsets: list[int] = []

        class StateStore:
            def get_update_offset(self) -> int:
                return 42

            def set_update_offset(self, value: int) -> None:
                offsets.append(value)

        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: None,
            answer_callback_query=lambda callback_query_id: None,
            update_offset_store=StateStore(),
        )
        bot.set_my_commands = lambda: None
        updates = [
            {"update_id": 43, "message": {"chat": {"id": 101}, "text": "/start"}},
            {"update_id": 44, "message": {"chat": {"id": 101}, "text": "/produk"}},
        ]

        def polling(offset: int = 0) -> list[dict[str, object]]:
            seen_offsets.append(offset)
            if len(seen_offsets) == 1:
                return updates
            raise KeyboardInterrupt

        bot.get_updates = polling
        bot.run()

        self.assertEqual([42, 45], seen_offsets)
        self.assertEqual([44, 45], offsets)

    def test_invalid_telegram_message_does_not_stop_processing(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        replies: list[str] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: replies.append(text),
            answer_callback_query=lambda callback_query_id: None,
        )

        bot.handle_update({"callback_query": {"id": "cb-1", "data": "/produk"}})
        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/cekstatus"}})
        bot.handle_update({"message": {"chat": {"id": 101}, "text": "normal message"}})

        self.assertEqual("Format: /status <invoice>", replies[0])
        self.assertEqual("Perintah tidak dikenal. Gunakan /help.", replies[1])

    def test_internal_message_fallback_when_html_is_rejected(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: None,
            answer_callback_query=lambda callback_query_id: None,
        )
        payloads: list[bytes] = []
        responses = iter([
            urllib.error.HTTPError("", 400, "Bad Request", {}, FakeResponse(b'{"ok":false}')),
            FakeResponse(b'{"ok":true}'),
        ])

        def fake_urlopen(request, timeout=0):
            payloads.append(request.data)
            response = next(responses)
            if isinstance(response, Exception):
                raise response
            return response

        with patch('modules.telegram_store.bot.urllib.request.urlopen', side_effect=fake_urlopen):
            bot._send_message(101, "<b>Agensi <script>alert('x')</script></b>")

        self.assertEqual(2, len(payloads))
        self.assertIn("Agensi alert('x')", payloads[1].decode())

    def test_health_command_reports_component_status(self) -> None:
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[tuple[int, str]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
            answer_callback_query=lambda callback_query_id: None,
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/health"}})

        self.assertIn("<b>Status Bot</b>", sent[0][1])
        self.assertIn("Polling: <b>OK</b>", sent[0][1])
        self.assertIn("Digiflazz: <b>OK</b>", sent[0][1])
        self.assertIn("Mode: <b>Production</b>", sent[0][1])

    def test_health_command_reports_cache_and_state_db(self) -> None:
        class FakeCatalog:
            def get_all(self) -> list[dict[str, object]]:
                return [{"buyer_sku_code": "SKU1"}, {"buyer_sku_code": "SKU2"}]

        class FakeStateStore:
            def get_update_offset(self) -> int:
                return 123

        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        service.catalog = FakeCatalog()
        sent: list[tuple[int, str]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            update_offset_store=FakeStateStore(),
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
            answer_callback_query=lambda callback_query_id: None,
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/health"}})

        self.assertIn("Cache produk: <b>2 produk</b>", sent[0][1])
        self.assertIn("State DB: <b>OK</b>", sent[0][1])
        self.assertIn("Update offset: <code>123</code>", sent[0][1])

    def test_health_command_reports_digiflazz_failure_without_crash(self) -> None:
        class FailingDigiflazz(FakeDigiflazz):
            def balance(self) -> int:
                raise RuntimeError("Digiflazz unavailable")

        service = TelegramStoreService(FailingDigiflazz(), markup_percent=10)
        sent: list[tuple[int, str]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
            answer_callback_query=lambda callback_query_id: None,
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/health"}})

        self.assertIn("Digiflazz: <b>Gagal</b>", sent[0][1])

    def test_health_command_reports_database_integrity(self) -> None:
        from modules.telegram_store.store import SQLiteOrderStore
        import tempfile as temp

        path = temp.TemporaryDirectory().name + ".sqlite3"
        store = SQLiteOrderStore(path)
        service = TelegramStoreService(FakeDigiflazz(), markup_percent=10)
        sent: list[tuple[int, str]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            update_offset_store=store,
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
            answer_callback_query=lambda callback_query_id: None,
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/health"}})

        self.assertIn("Integritas DB: <b>OK</b>", sent[0][1])

    def test_provider_runtime_error_is_reported_to_user_without_crash(self) -> None:
        class FailingDigiflazz(FakeDigiflazz):
            def create_transaction(self, buyer_sku_code: str, customer_no: str, ref_id: str, testing: bool = False) -> dict[str, object]:
                raise RuntimeError("Digiflazz connection failed")

        service = TelegramStoreService(FailingDigiflazz(balance=1_000_000), markup_percent=10)
        sent: list[tuple[int, str]] = []
        bot = TelegramStoreBot(
            token="token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text)),
            answer_callback_query=lambda callback_query_id: None,
        )

        bot.handle_update({"message": {"chat": {"id": 101}, "text": "/beli BRIZZI5 081234554320"}})

        self.assertIn("Digiflazz gagal diproses", sent[-1][1])

    def test_health_command_is_registered_for_slash_menu(self) -> None:
        commands = {item['command'] for item in BOT_COMMANDS}

        self.assertIn('health', commands)

    def test_load_env_file_sets_missing_bot_config(self) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as handle:
            handle.write(
                "TELEGRAM_BOT_TOKEN=token-abc\n"
                "DIGIFLAZZ_USERNAME=store-user\n"
                "DIGIFLAZZ_API_KEY=api-key\n"
            )
            path = handle.name
        try:
            os.environ.pop("TELEGRAM_BOT_TOKEN", None)
            os.environ.pop("DIGIFLAZZ_USERNAME", None)
            os.environ.pop("DIGIFLAZZ_API_KEY", None)
            load_env_file(path)
            self.assertEqual(os.environ["TELEGRAM_BOT_TOKEN"], "token-abc")
            self.assertEqual(os.environ["DIGIFLAZZ_USERNAME"], "store-user")
            self.assertEqual(os.environ["DIGIFLAZZ_API_KEY"], "api-key")
        finally:
            os.unlink(path)

    def test_build_bot_from_env_uses_hn_assistent_bot(self) -> None:
        env_path = Path(tempfile.gettempdir()) / "telegram_store_test.env"
        env_path.write_text(
            "TELEGRAM_BOT_TOKEN=token-abc\n"
            "TELEGRAM_BOT_USERNAME=@hn_assistent_bot\n"
            "DIGIFLAZZ_USERNAME=store-user\n"
            "DIGIFLAZZ_API_KEY=api-key\n",
            encoding="utf-8",
        )
        try:
            os.environ.pop("TELEGRAM_BOT_TOKEN", None)
            os.environ.pop("TELEGRAM_BOT_USERNAME", None)
            os.environ.pop("DIGIFLAZZ_USERNAME", None)
            os.environ.pop("DIGIFLAZZ_API_KEY", None)
            bot = build_bot_from_env(env_path=env_path)
            self.assertEqual(bot.bot_username, "@hn_assistent_bot")
        finally:
            env_path.unlink(missing_ok=True)

    def test_build_bot_from_env_configures_hermes_status(self) -> None:
        env_path = Path(tempfile.gettempdir()) / 'telegram_store_hermes.env'
        hermes_home = Path(tempfile.gettempdir()) / 'hermes_status_home_test'
        env_values = [
            'TELEGRAM_BOT_TOKEN=token-abc',
            'DIGIFLAZZ_USERNAME=store-user',
            'DIGIFLAZZ_API_KEY=api-key',
            'TRELLO_API_KEY=trello-key',
            'TRELLO_TOKEN=trello-token',
            'HERMES_BIN=hermes-test.exe',
            'HERMES_WORKDIR=D:/projects/klinik-git',
            'HERMES_PROVIDER_BASE_URL=http://127.0.0.1:20128/v1',
            'HERMES_PROVIDER_API_KEY=provider-key',
            'HERMES_PROVIDER_MODEL=cd',
            'HERMES_CHAT_TIMEOUT_SECONDS=900',
        ]
        env_path.write_text(os.linesep.join(env_values), encoding='utf-8')
        env_keys = [
            'TELEGRAM_BOT_TOKEN',
            'DIGIFLAZZ_USERNAME',
            'DIGIFLAZZ_API_KEY',
            'TRELLO_API_KEY',
            'TRELLO_TOKEN',
            'TRELLO_PROGRESS_LIST_ID',
            'HERMES_HOME',
            'HERMES_BIN',
            'HERMES_WORKDIR',
            'HERMES_PROVIDER_BASE_URL',
            'HERMES_PROVIDER_API_KEY',
            'HERMES_PROVIDER_MODEL',
            'HERMES_CHAT_TIMEOUT_SECONDS',
        ]
        try:
            for key in env_keys:
                os.environ.pop(key, None)
            os.environ['HERMES_HOME'] = str(hermes_home)
            bot = build_bot_from_env(env_path=env_path)

            self.assertIsInstance(bot.hermes_status, HermesStatusProvider)
            assert bot.hermes_status is not None
            self.assertEqual(bot.hermes_status.delegation_root, hermes_home / 'cache' / 'delegation' / 'live')
            self.assertEqual(bot.live_interval, 5.0)
            self.assertEqual(bot.live_duration_seconds, 60.0)
            assert bot.hermes_status is not None
            self.assertEqual(bot.hermes_status.agent_log_path, hermes_home / 'logs' / 'agent.log')
            self.assertIsInstance(bot.hermes_chat, HermesChatClient)
            assert bot.hermes_chat is not None
            self.assertEqual(bot.hermes_chat.hermes_binary, 'hermes-test.exe')
            self.assertEqual(bot.hermes_chat.workdir, Path('D:/projects/klinik-git'))
            self.assertEqual(bot.hermes_chat.status_provider, bot.hermes_status)
            self.assertEqual(bot.hermes_chat.provider_model, 'cd')
            self.assertEqual(bot.hermes_chat.timeout, 900.0)
        finally:
            env_path.unlink(missing_ok=True)
            for key in env_keys:
                os.environ.pop(key, None)

    def test_build_bot_from_env_defaults_hermes_timeout_to_900(self) -> None:
        env_path = Path(tempfile.gettempdir()) / 'telegram_store_hermes_default_timeout.env'
        env_path.write_text('TELEGRAM_BOT_TOKEN=token-abc\n', encoding='utf-8')
        try:
            os.environ.pop('TELEGRAM_BOT_TOKEN', None)
            os.environ.pop('HERMES_CHAT_TIMEOUT_SECONDS', None)
            bot = build_bot_from_env(env_path=env_path)

            self.assertEqual(bot.hermes_chat.timeout, 900.0)
            self.assertTrue(bot.hermes_chat.hermes_binary.endswith('hermes-hidden.cmd'))
        finally:
            env_path.unlink(missing_ok=True)
            os.environ.pop('TELEGRAM_BOT_TOKEN', None)
            os.environ.pop('HERMES_CHAT_TIMEOUT_SECONDS', None)

    def test_post_provider_uses_configured_hermes_timeout(self) -> None:
        env_path = Path(tempfile.gettempdir()) / 'telegram_store_provider_timeout.env'
        env_path.write_text(
            'HERMES_PROVIDER_BASE_URL=http://127.0.0.1:20128/v1\n'
            'HERMES_PROVIDER_API_KEY=provider-key\n'
            'HERMES_CHAT_TIMEOUT_SECONDS=777\n',
            encoding='utf-8',
        )
        env_keys = [
            'HERMES_PROVIDER_BASE_URL',
            'HERMES_PROVIDER_API_KEY',
            'HERMES_CHAT_TIMEOUT_SECONDS',
        ]
        try:
            for key in env_keys:
                os.environ.pop(key, None)
            load_env_file(env_path)
            with patch('modules.telegram_store.cli.urllib.request.urlopen') as fake_urlopen:
                fake_urlopen.return_value = FakeResponse(b'{"ok": true}')
                result = _post_provider({'model': 'cd'})

            self.assertEqual(result, {'ok': True})
            self.assertEqual(fake_urlopen.call_args.kwargs['timeout'], 777.0)
        finally:
            env_path.unlink(missing_ok=True)
            for key in env_keys:
                os.environ.pop(key, None)

    def test_run_hermes_command_hides_console_window(self) -> None:
        expected_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        with patch('modules.telegram_store.cli.subprocess.run') as fake_run:
            _run_hermes_command(['hermes'], b'query', 1)

        self.assertEqual(fake_run.call_args.kwargs.get('creationflags'), expected_flags)

    def test_build_bot_from_env_allows_missing_digiflazz(self) -> None:
        env_path = Path(tempfile.gettempdir()) / "telegram_store_no_digiflazz.env"
        env_path.write_text("TELEGRAM_BOT_TOKEN=token-abc\n", encoding="utf-8")
        try:
            os.environ.pop("TELEGRAM_BOT_TOKEN", None)
            os.environ.pop("DIGIFLAZZ_USERNAME", None)
            os.environ.pop("DIGIFLAZZ_API_KEY", None)
            bot = build_bot_from_env(env_path=env_path)

            self.assertEqual(bot.bot_username, "@hn_assistent_bot")
            sent: list[tuple[int, str]] = []
            bot.send_message = lambda chat_id, text, reply_markup=None: sent.append((chat_id, text))
            bot.handle_update({"message": {"chat": {"id": 101}, "text": "/start"}})
            bot.handle_update({"message": {"chat": {"id": 101}, "text": "/produk"}})
            bot.handle_update({"message": {"chat": {"id": 101}, "text": "/saldo"}})

            self.assertIn("Selamat datang", sent[0][1])
            self.assertIn("Produk tidak ditemukan", sent[2][1]) if bot.service.catalog is None or not bot.service.catalog.get_all() else self.assertIn("<b>Daftar Produk</b>", sent[2][1])
            self.assertIn("Saldo saat ini", sent[-1][1])
        finally:
            env_path.unlink(missing_ok=True)
