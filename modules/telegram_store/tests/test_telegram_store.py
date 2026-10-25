from __future__ import annotations

import json
import os
import subprocess
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
from modules.telegram_store.bot import BOT_COMMANDS


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
    def __init__(self) -> None:
        self.orders: list[tuple[str, str, str]] = []

    def balance(self) -> int:
        return 250_000

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

    def test_store_lists_products_with_markup_and_orders_as_buyer(self) -> None:
        digiflazz = FakeDigiflazz()
        orders = InMemoryOrderStore()
        service = TelegramStoreService(digiflazz, markup_percent=10, orders=orders)

        products = service.list_products("PLN")
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]["sale_price"], 12_650)

        order = service.order("BRIZZI5", "08123456789")
        self.assertTrue(order["invoice"].startswith("HN-"))
        self.assertEqual(order["status"], "Pending")
        self.assertEqual(digiflazz.orders[0][0], "BRIZZI5")
        self.assertEqual(digiflazz.orders[0][1], "08123456789")
        self.assertEqual(orders.find(order["invoice"])["invoice"], order["invoice"])

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
        self.assertIn("Brizzi 5", sent[1][1])
        self.assertIn("Rp 6.820", sent[1][1])
        self.assertIn(purchase["invoice"], sent[2][1])

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

        self.assertIn("Brizzi 5", sent[0][1])

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
        self.assertIn("Brizzi 5", sent[1][1])
        self.assertIn(purchase["invoice"], sent[2][1])

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

        markup = sent[0][2]
        self.assertIsNotNone(markup)
        rows = markup["inline_keyboard"]
        self.assertEqual(len(rows), 5)
        self.assertEqual(len(rows[0]), 2)
        self.assertEqual(len(rows[1]), 1)
        row_texts = {button["text"] for row in rows for button in row}
        self.assertIn("Lihat Produk", row_texts)
        self.assertIn("Beli Produk", row_texts)
        self.assertIn("Cek Status", row_texts)
        self.assertNotIn("Saldo", row_texts)

    def test_start_shows_hermes_monitoring_buttons(self) -> None:
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

        markup = sent[0][2]
        assert markup is not None
        rows = markup['inline_keyboard']
        self.assertEqual(
            rows[-2],
            [
                {'text': 'Hermes Live', 'callback_data': '/hermeslive'},
                {'text': 'Stop Live', 'callback_data': '/hermesstop'},
            ],
        )
        self.assertEqual(
            rows[-1],
            [
                {'text': 'Hubungi Hermes', 'callback_data': '/hubungihermes'},
                {'text': 'Tutup Hermes', 'callback_data': '/akhirihermes'},
            ],
        )

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

        markup = sent[0][2]
        assert markup is not None
        row_texts = {button['text'] for row in markup['inline_keyboard'] for button in row}
        self.assertIn('Lihat Produk', row_texts)
        self.assertIn('Status Hermes', row_texts)

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

        self.assertIn("Brizzi 5", sent[0][1])
        self.assertEqual(answered, ["cb-1"])

    def test_bot_commands_include_hermes_status(self) -> None:
        commands = {item['command']: item['description'] for item in BOT_COMMANDS}

        self.assertEqual(commands['hermes'], 'Status Hermes')
        self.assertEqual(commands['hermeslive'], 'Monitoring Hermes realtime')
        self.assertEqual(commands['hermesstop'], 'Hentikan monitoring Hermes')
        self.assertEqual(commands['hubungihermes'], 'Hubungi Hermes')

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
        self.assertIn(b'Lihat daftar produk', request.data)
        self.assertNotIn(b'"saldo"', request.data)

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
        with self.assertRaises(KeyboardInterrupt):
            bot.run()

        self.assertEqual(calls, ["commands"])

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
            self.assertIn("Produk tidak ditemukan", sent[1][1])
            self.assertIn("belum tersedia", sent[2][1])
        finally:
            env_path.unlink(missing_ok=True)
