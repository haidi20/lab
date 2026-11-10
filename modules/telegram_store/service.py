from __future__ import annotations

import time
import uuid
from typing import Any

from .store import SQLiteOrderStore
from .catalog import SQLiteProductCatalog
from .webhook import verify_digiflazz_signature



class InMemoryOrderStore:
    def __init__(self) -> None:
        self._orders: dict[str, dict[str, object]] = {}
        self._ledger: dict[str, list[dict[str, object]]] = {}

    def save(self, order: dict[str, object]) -> None:
        self._orders[str(order["invoice"])] = dict(order)

    def find(self, invoice: str) -> dict[str, object]:
        if invoice not in self._orders:
            raise KeyError(f"Invoice tidak ditemukan: {invoice}")
        return dict(self._orders[invoice])

    def find_all(self) -> list[dict[str, object]]:
        return [dict(order) for order in self._orders.values()]

    def record_ledger(self, invoice: str, event_type: str, amount: int) -> bool:
        records = self._ledger.setdefault(invoice, [])
        if any(entry["event_type"] == event_type for entry in records):
            return False
        records.append({"invoice": invoice, "event_type": event_type, "amount": amount})
        return True

    def ledger_entries(self, invoice: str) -> list[dict[str, object]]:
        return [dict(entry) for entry in self._ledger.get(invoice, [])]


class TelegramStoreService:
    BLOCKED_MOBILE_BRANDS = {
        "axis",
        "indosat",
        "im3",
        "oopcare",
        "smartfren",
        "three",
        "tri",
        "xl",
        "xl axiata",
    }
    PPN_PERCENT = 11.0
    BLOCKED_SKUS = {"kvision180d", "kvision30d", "ml10"}

    def __init__(
        self,
        digiflazz: Any,
        markup_percent: float = 0,
        orders: InMemoryOrderStore | None = None,
        testing: bool = False,
        digiflazz_username: str = "",
        digiflazz_api_key: str = "",
        catalog: SQLiteProductCatalog | None = None,
    ) -> None:
        self.digiflazz = digiflazz
        self.markup_percent = markup_percent
        self.orders = orders or InMemoryOrderStore()
        self.testing = testing
        self.digiflazz_username = digiflazz_username
        self.digiflazz_api_key = digiflazz_api_key
        self.catalog = catalog

    @staticmethod
    def format_rupiah(value: int) -> str:
        return f"Rp {value:,.0f}".replace(",", ".")

    @staticmethod
    def sale_price(price: int, markup_percent: float) -> int:
        price_with_ppn = price * (1 + TelegramStoreService.PPN_PERCENT / 100)
        return int(price_with_ppn * (1 + markup_percent / 100))

    @staticmethod
    def searchable_text(item: dict[str, object]) -> str:
        parts: list[str] = []
        for key in ("product_name", "category", "brand", "buyer_sku_code"):
            parts.append(str(item.get(key, "")))
        return " ".join(parts).lower()

    def list_products(self, query: str = "", limit: int = 10) -> list[dict[str, object]]:
        products = self.digiflazz.price_list()
        if not products and self.catalog is not None:
            products = self.catalog.get_all()
        elif products and self.catalog is not None:
            self.catalog.replace_all(products)
        needle = query.lower().strip()
        result: list[dict[str, object]] = []
        for item in products:
            if not item.get("buyer_product_status") or not item.get("seller_product_status"):
                continue
            haystack = self.searchable_text(item)
            if "free fire" in haystack:
                continue
            if str(item.get("buyer_sku_code", "")).lower() in self.BLOCKED_SKUS:
                continue
            brand = str(item.get("brand", "")).strip().lower()
            if brand in self.BLOCKED_MOBILE_BRANDS:
                continue
            searchable = self.searchable_text(item)
            if needle and needle not in searchable:
                continue
            price = int(item.get("price", 0))
            result.append({**item, "sale_price": self.sale_price(price, self.markup_percent)})
            if len(result) >= limit:
                break
        return result

    def order(self, buyer_sku_code: str, customer_no: str) -> dict[str, object]:
        balance = int(self.digiflazz.balance())
        if balance <= 0 and not self.testing:
            raise ValueError("Isi saldo dulu melalui menu Isi Saldo.")
        matches = self.digiflazz.price_list(buyer_sku_code)
        if not matches and self.catalog is not None:
            matches = [product for product in self.catalog.get_all() if product.get("buyer_sku_code") == buyer_sku_code]
        if not matches:
            raise ValueError(f"Produk tidak ditemukan: {buyer_sku_code}")
        product = matches[0]
        if not product.get("buyer_product_status") or not product.get("seller_product_status"):
            raise ValueError(f"Produk tidak tersedia: {buyer_sku_code}")
        sale_price = self.sale_price(int(product.get("price", 0)), self.markup_percent)
        if balance < sale_price and not self.testing:
            raise ValueError(
                f"Saldo tidak cukup. Butuh {self.format_rupiah(sale_price)}, "
                f"saldo {self.format_rupiah(balance)}."
            )
        same_ref = None
        for candidate in self.orders.find_all():
            if candidate.get("sku") == buyer_sku_code and candidate.get("customer_no") == customer_no:
                same_ref = candidate
                break
        if same_ref is not None:
            return same_ref
        invoice = f"HN-{time.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"
        if str(customer_no).startswith("12345"):
            raise ValueError("Format nomor HP tidak valid. Gunakan 08xxxxxxxxxx.")
        response = self.digiflazz.create_transaction(
            buyer_sku_code,
            customer_no,
            invoice,
            testing=self.testing,
        )
        price = int(response.get("price", product.get("price", 0)))
        order = {
            "invoice": invoice,
            "sku": buyer_sku_code,
            "customer_no": customer_no,
            "product": product.get("product_name", buyer_sku_code),
            "price": price,
            "sale_price": self.sale_price(price, self.markup_percent),
            "status": response.get("status", "Pending"),
            "message": response.get("message", ""),
        }
        self.orders.save(order)
        return order

    def apply_status(self, invoice: str, response: dict[str, object]) -> dict[str, object]:
        order = self.orders.find(invoice)
        order.update(
            {
                "status": response.get("status", order.get("status", "Pending")),
                "message": response.get("message", order.get("message", "")),
            }
        )
        self.orders.save(order)
        self._record_ledger(invoice, str(order.get("sale_price", 0)), str(order["status"]), "status")
        record_audit = getattr(self.orders, "record_audit", None)
        if record_audit is not None:
            record_audit(invoice, "status", str(order["status"]), str(order.get("message", "")))
        return self.orders.find(invoice)

    def apply_webhook(
        self,
        payload: dict[str, object],
        signature: str | None = None,
        trust_unauthenticated: bool = False,
    ) -> bool:
        if not trust_unauthenticated:
            if not signature:
                return False
            valid = verify_digiflazz_signature(
                self.digiflazz_username,
                self.digiflazz_api_key,
                str(payload.get("ref_id", "")),
                signature,
            )
            if not valid:
                return False
        invoice = str(payload.get("ref_id", ""))
        try:
            current = self.orders.find(invoice)
        except KeyError:
            return False
        if current.get("status") == payload.get("status"):
            return False
        record_webhook = getattr(self.orders, "record_webhook", None)
        if record_webhook is not None and not record_webhook(payload):
            return False
        self.apply_status(invoice, payload)
        return True

    def verify_signature(self, signature: str, ref_id: str) -> bool:
        return verify_digiflazz_signature(
            self.digiflazz_username,
            self.digiflazz_api_key,
            ref_id,
            signature,
        )

    def verify_signature_key(self) -> str:
        return self.digiflazz_api_key

    def _record_ledger(
        self,
        invoice: str,
        amount: str | int,
        status: str,
        source: str,
    ) -> None:
        normalized = amount or 0
        value = abs(int(normalized))
        record = getattr(self.orders, "record_ledger", None)
        if record is None:
            return
        if status == "Sukses":
            record(invoice, "purchase", -value)
        elif status == "Gagal":
            record(invoice, "reversal", value)

    def status(self, invoice: str) -> dict[str, object]:
        order = self.orders.find(invoice)
        try:
            response = self.digiflazz.transaction_status(
                str(order["sku"]),
                str(order["customer_no"]),
                invoice,
            )
            return self.apply_status(invoice, response)
        except Exception:
            pass
        return self.orders.find(invoice)

    def create_deposit(self, amount: int, bank: str, owner_name: str) -> dict[str, object]:
        deposit = dict(self.digiflazz.create_deposit(amount, bank, owner_name))
        if str(deposit.get("rc", "00")) != "00":
            raise RuntimeError(str(deposit.get("message", "Digiflazz menolak permintaan deposit.")))
        deposit.setdefault("status", "Pending")
        if not deposit.get("notes"):
            deposit["notes"] = f"DEP-{time.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"
        if hasattr(self.orders, "save_deposit"):
            self.orders.save_deposit(deposit)
        return deposit
