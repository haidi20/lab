from __future__ import annotations

import json
import os
import unittest
import urllib.error
import urllib.request
from time import sleep
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

from modules.telegram_store.bot import load_env_file
from modules.telegram_store.client import DigiflazzClient
from modules.telegram_store.service import TelegramStoreService
from modules.telegram_store.store import SQLiteOrderStore
from modules.telegram_store.bot import SANDBOX_BANKS


PREPAID_CASES: list[tuple[str, str]] = [
    ("087800001230", "Sukses"),
    ("087800001232", "Gagal"),
    ("087800001233", "Pending"),
    ("087800001234", "Pending"),
]

# customer_no, inquiry_status, payment_status (None = jangan panggil payment)
POSTPAID_CASES: dict[str, list[tuple[str, str, str | None]]] = {
    "pln": [
        ("530000000001", "Sukses", "Sukses"),
        ("530000000003", "Gagal", None),
        ("530000000006", "Sukses", "Gagal"),
        ("630000000001", "Sukses", "Pending"),
    ],
    "pdam": [
        ("1013226", "Sukses", "Sukses"),
        ("1013227", "Gagal", None),
        ("1013230", "Sukses", "Gagal"),
        ("2013226", "Sukses", "Pending"),
    ],
    "internet": [
        ("6391601001", "Sukses", "Sukses"),
        ("6391601002", "Gagal", None),
        ("6391601005", "Sukses", "Gagal"),
        ("7391601001", "Sukses", "Pending"),
    ],
    "bpjs": [
        ("8801234560001", "Sukses", "Sukses"),
        ("8801234560002", "Gagal", None),
        ("8801234560005", "Sukses", "Gagal"),
        ("9801234560001", "Sukses", "Pending"),
    ],
    "multifinance": [
        ("6391601201", "Sukses", "Sukses"),
        ("6391601202", "Gagal", None),
        ("6391601205", "Sukses", "Gagal"),
        ("7391601201", "Sukses", "Pending"),
    ],
    "cimahi": [
        ("329801092375999991", "Sukses", "Sukses"),
        ("329801092375999992", "Gagal", None),
        ("329801092375999995", "Sukses", "Gagal"),
        ("429801092375999991", "Sukses", "Pending"),
    ],
    "pdl": [
        ("3298010921", "Sukses", "Sukses"),
        ("3298010922", "Gagal", None),
        ("3298010923", "Sukses", "Gagal"),
        ("4298010921", "Sukses", "Pending"),
    ],
    "pgas": [
        ("0110014601", "Sukses", "Sukses"),
        ("0110014603", "Gagal", None),
        ("0110014605", "Sukses", "Gagal"),
        ("1110014601", "Sukses", "Pending"),
    ],
    "tv": [
        ("127246500101", "Sukses", "Sukses"),
        ("127246500102", "Gagal", None),
        ("127246500105", "Sukses", "Gagal"),
        ("227246500101", "Sukses", "Pending"),
    ],
    "bpjstk": [
        ("8102051011270001", "Sukses", "Sukses"),
        ("8102051011270002", "Gagal", None),
        ("8102051011270003", "Sukses", "Gagal"),
        ("9102051011270001", "Sukses", "Pending"),
    ],
    "bpjstkpu": [
        ("400000100001", "Sukses", "Sukses"),
        ("400000100002", "Gagal", None),
        ("400000100003", "Sukses", "Gagal"),
        ("500000100001", "Sukses", "Pending"),
    ],
    "plnnontaglist": [
        ("3225030005921", "Sukses", "Sukses"),
        ("3225030005922", "Gagal", None),
        ("3225030005923", "Sukses", "Gagal"),
        ("4225030005921", "Sukses", "Pending"),
    ],
    "emoney": [
        ("082100000001", "Sukses", "Sukses"),
        ("082100000002", "Gagal", None),
        ("082100000003", "Sukses", "Gagal"),
        ("082110000001", "Sukses", "Pending"),
    ],
    "samsat": [
        ("9658548523568701,0212502110170100", "Sukses", "Sukses"),
        ("9658548523568702,0212502110170100", "Gagal", None),
        ("9658548523568705,0212502110170100", "Sukses", "Gagal"),
        ("0658548523568701,0212502110170100", "Sukses", "Pending"),
    ],
    "hp": [
        ("081234554320", "Sukses", "Sukses"),
        ("081234554321", "Gagal", None),
        ("081234554324", "Sukses", "Gagal"),
        ("081244554320", "Sukses", "Pending"),
    ],
}


class DigiflazzSandboxRealTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        load_env_file(".env")
        cls.username = os.environ.get("DIGIFLAZZ_USERNAME", "")
        cls.production_key = os.environ.get("DIGIFLAZZ_API_KEY", "")
        cls.development_key = os.environ.get("DIGIFLAZZ_DEVELOPMENT_KEY", "")
        if not all([cls.username, cls.production_key, cls.development_key]):
            raise unittest.SkipTest("Kredensial sandbox Digiflazz belum lengkap")

        cls.client = DigiflazzClient(
            username=cls.username,
            api_key=cls.production_key,
            development_key=cls.development_key,
        )
        cls.client.set_mode("sandbox")
        if os.environ.get("DIGIFLAZZ_REAL_TESTS", "0") != "1":
            raise unittest.SkipTest("Real Digiflazz tests require DIGIFLAZZ_REAL_TESTS=1")

    def request(self, payload: dict[str, object]) -> dict[str, object]:
        request = urllib.request.Request(
            f"{self.client.base_url}/v1/transaction",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
        except urllib.error.HTTPError as error:
            raw = error.read()
        return json.loads(raw.decode("utf-8"))

    def prepaid(self, customer_no: str, expected_status: str) -> None:
        ref_id = "HN-TDD-" + uuid.uuid4().hex[:12].upper()
        response = self.request(
            {
                "username": self.client.username,
                "buyer_sku_code": "xld10",
                "customer_no": customer_no,
                "ref_id": ref_id,
                "testing": True,
                "sign": self.client._sign(ref_id),
            }
        )["data"]
        self.assertEqual(response["ref_id"], ref_id)
        self.assertEqual(response["status"], expected_status)

    def price_list_with_limit_retry(self) -> list[dict[str, object]]:
        for attempt in range(2):
            products = self.client.price_list()
            if products:
                return products
            if attempt == 0:
                sleep(61)
        self.fail("Digiflazz masih membatasi price list setelah dua percobaan")

    def postpaid(
        self,
        sku: str,
        customer_no: str,
        inquiry_status: str,
        payment_status: str | None,
    ) -> None:
        ref_id = "HN-TDD-" + uuid.uuid4().hex[:12].upper()
        base = {
            "username": self.client.username,
            "buyer_sku_code": sku,
            "customer_no": customer_no,
            "ref_id": ref_id,
            "testing": True,
            "sign": self.client._sign(ref_id),
        }
        inquiry = self.request({**base, "commands": "inq-pasca"})["data"]
        self.assertEqual(inquiry["ref_id"], ref_id)
        self.assertEqual(inquiry["status"], inquiry_status)

        if payment_status is None:
            return

        payment = self.request({**base, "commands": "pay-pasca"})["data"]
        self.assertEqual(payment["ref_id"], ref_id)
        self.assertEqual(payment["status"], payment_status)

    def test_sandbox_real_prepaid_all_statuses(self) -> None:
        for customer_no, expected in PREPAID_CASES:
            with self.subTest(customer_no=customer_no):
                self.prepaid(customer_no, expected)

    def test_sandbox_real_pln(self) -> None:
        for customer_no, inquiry_status, payment_status in POSTPAID_CASES["pln"]:
            with self.subTest(customer_no=customer_no):
                self.postpaid("pln", customer_no, inquiry_status, payment_status)

    def test_sandbox_real_pdam(self) -> None:
        for customer_no, inquiry_status, payment_status in POSTPAID_CASES["pdam"]:
            with self.subTest(customer_no=customer_no):
                self.postpaid("pdam", customer_no, inquiry_status, payment_status)

    def test_sandbox_real_internet(self) -> None:
        for customer_no, inquiry_status, payment_status in POSTPAID_CASES["internet"]:
            with self.subTest(customer_no=customer_no):
                self.postpaid("internet", customer_no, inquiry_status, payment_status)

    def test_sandbox_real_bpjs(self) -> None:
        for customer_no, inquiry_status, payment_status in POSTPAID_CASES["bpjs"]:
            with self.subTest(customer_no=customer_no):
                self.postpaid("bpjs", customer_no, inquiry_status, payment_status)

    def test_sandbox_real_multifinance(self) -> None:
        for customer_no, inquiry_status, payment_status in POSTPAID_CASES["multifinance"]:
            with self.subTest(customer_no=customer_no):
                self.postpaid("multifinance", customer_no, inquiry_status, payment_status)

    def test_sandbox_real_cimahi(self) -> None:
        for customer_no, inquiry_status, payment_status in POSTPAID_CASES["cimahi"]:
            with self.subTest(customer_no=customer_no):
                self.postpaid("cimahi", customer_no, inquiry_status, payment_status)

    def test_sandbox_real_pdl(self) -> None:
        for customer_no, inquiry_status, payment_status in POSTPAID_CASES["pdl"]:
            with self.subTest(customer_no=customer_no):
                self.postpaid("pdl", customer_no, inquiry_status, payment_status)

    def test_sandbox_real_pgas(self) -> None:
        for customer_no, inquiry_status, payment_status in POSTPAID_CASES["pgas"]:
            with self.subTest(customer_no=customer_no):
                self.postpaid("pgas", customer_no, inquiry_status, payment_status)

    def test_sandbox_real_tv(self) -> None:
        for customer_no, inquiry_status, payment_status in POSTPAID_CASES["tv"]:
            with self.subTest(customer_no=customer_no):
                self.postpaid("tv", customer_no, inquiry_status, payment_status)

    def test_sandbox_real_bpjstk(self) -> None:
        for customer_no, inquiry_status, payment_status in POSTPAID_CASES["bpjstk"]:
            with self.subTest(customer_no=customer_no):
                self.postpaid("bpjstk", customer_no, inquiry_status, payment_status)

    def test_sandbox_real_bpjstkpu(self) -> None:
        for customer_no, inquiry_status, payment_status in POSTPAID_CASES["bpjstkpu"]:
            with self.subTest(customer_no=customer_no):
                self.postpaid("bpjstkpu", customer_no, inquiry_status, payment_status)

    def test_sandbox_real_plnnontaglist(self) -> None:
        for customer_no, inquiry_status, payment_status in POSTPAID_CASES["plnnontaglist"]:
            with self.subTest(customer_no=customer_no):
                self.postpaid("plnnontaglist", customer_no, inquiry_status, payment_status)

    def test_sandbox_real_emoney(self) -> None:
        for customer_no, inquiry_status, payment_status in POSTPAID_CASES["emoney"]:
            with self.subTest(customer_no=customer_no):
                self.postpaid("emoney", customer_no, inquiry_status, payment_status)

    def test_sandbox_real_samsat(self) -> None:
        for customer_no, inquiry_status, payment_status in POSTPAID_CASES["samsat"]:
            with self.subTest(customer_no=customer_no):
                self.postpaid("samsat", customer_no, inquiry_status, payment_status)

    def test_sandbox_real_hp(self) -> None:
        for customer_no, inquiry_status, payment_status in POSTPAID_CASES["hp"]:
            with self.subTest(customer_no=customer_no):
                self.postpaid("hp", customer_no, inquiry_status, payment_status)

    def test_sandbox_real_deposit_each_supported_bank(self) -> None:
        self.assertEqual(("Flip", "ShopeePay"), SANDBOX_BANKS)
        for bank in SANDBOX_BANKS:
            with self.subTest(bank=bank):
                ticket = self.client.create_deposit(200_000, bank, "Sandbox Real Bank Test")
                self.assertEqual(ticket.get("rc"), "00")
                self.assertIn(bank, str(ticket.get("bank", "")))
                self.assertTrue(str(ticket.get("account_no", "")))

    def test_sandbox_real_payment_infrastructure_flow(self) -> None:
        with TemporaryDirectory() as directory:
            service = TelegramStoreService(
                self.client,
                orders=SQLiteOrderStore(Path(directory) / "orders.sqlite3"),
                markup_percent=10,
                digiflazz_username=self.username,
                digiflazz_api_key=self.development_key,
            )
            ref_id = f"HN-INFRA-{uuid.uuid4().hex[:12].upper()}"
            provider = self.client.create_transaction("xld10", "087800001232", ref_id, testing=True)
            initial = {
                "invoice": ref_id,
                "sku": "xld10",
                "customer_no": "087800001232",
                "product": "Sandbox Payment Infrastructure",
                "price": 10_000,
                "sale_price": 11_000,
                "status": provider.get("status", "Pending"),
                "message": provider.get("message", ""),
            }
            service.orders.save(initial)
            status = str(provider.get("status", ""))
            self.assertIn(status, {"Sukses", "Gagal", "Pending"})

            service.apply_status(ref_id, provider)
            service.apply_status(ref_id, provider)
            entries = service.orders.ledger_entries(ref_id)

            self.assertEqual(status, service.orders.find(ref_id)["status"])
            self.assertEqual(1, len(entries))
            if status == "Sukses":
                self.assertLess(entries[0]["amount"], 0)
            elif status == "Gagal":
                self.assertGreater(entries[0]["amount"], 0)

            refreshed = self.client.transaction_status("xld10", "087800001232", ref_id)
            self.assertEqual(status, refreshed.get("status", status))

    def test_sandbox_real_purchase_every_product(self) -> None:
        products = self.price_list_with_limit_retry()
        self.assertEqual(74, len(products))
        customer_by_category = {
            "games": "1234567890",
            "gas": "0110014601",
            "pln": "530000000001",
            "tv": "127246500101",
        }
        default_customer = "081234554320"

        for product in products:
            sku = str(product.get("buyer_sku_code", ""))
            category = str(product.get("category", "")).lower()
            customer_no = customer_by_category.get(category, default_customer)
            if category == "e-money":
                customer_no = "082100000001"
            with self.subTest(sku=sku, category=product.get("category")):
                invoice = f"HN-ALL-{sku.upper()}-{uuid.uuid4().hex[:8].upper()}"
                response = self.client.create_transaction(
                    sku,
                    customer_no,
                    invoice,
                    testing=True,
                )

                self.assertEqual(invoice, response.get("ref_id"))
                self.assertIn(str(response.get("status", "")).lower(), {"sukses", "pending"})
