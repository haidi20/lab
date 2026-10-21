from __future__ import annotations

import time
import uuid
from typing import Any


class InMemoryOrderStore:
    def __init__(self) -> None:
        self._orders: dict[str, dict[str, object]] = {}

    def save(self, order: dict[str, object]) -> None:
        self._orders[str(order["invoice"])] = dict(order)

    def find(self, invoice: str) -> dict[str, object]:
        if invoice not in self._orders:
            raise KeyError(f"Invoice tidak ditemukan: {invoice}")
        return dict(self._orders[invoice])


class TelegramStoreService:
    def __init__(
        self,
        digiflazz: Any,
        markup_percent: float = 0,
        orders: InMemoryOrderStore | None = None,
        testing: bool = False,
    ) -> None:
        self.digiflazz = digiflazz
        self.markup_percent = markup_percent
        self.orders = orders or InMemoryOrderStore()
        self.testing = testing

    @staticmethod
    def format_rupiah(value: int) -> str:
        return f"Rp {value:,.0f}".replace(",", ".")

    @staticmethod
    def sale_price(price: int, markup_percent: float) -> int:
        return int(price * (1 + markup_percent / 100))

    def list_products(self, query: str = "", limit: int = 10) -> list[dict[str, object]]:
        products = self.digiflazz.price_list()
        needle = query.lower().strip()
        result: list[dict[str, object]] = []
        for item in products:
            if not item.get("buyer_product_status") or not item.get("seller_product_status"):
                continue
            searchable = " ".join(
                str(item.get(key, ""))
                for key in ("product_name", "category", "brand", "buyer_sku_code")
            ).lower()
            if needle and needle not in searchable:
                continue
            price = int(item.get("price", 0))
            result.append({**item, "sale_price": self.sale_price(price, self.markup_percent)})
            if len(result) >= limit:
                break
        return result

    def order(self, buyer_sku_code: str, customer_no: str) -> dict[str, object]:
        matches = self.digiflazz.price_list(buyer_sku_code)
        if not matches:
            raise ValueError(f"Produk tidak ditemukan: {buyer_sku_code}")
        product = matches[0]
        if not product.get("buyer_product_status") or not product.get("seller_product_status"):
            raise ValueError(f"Produk tidak tersedia: {buyer_sku_code}")
        invoice = f"HN-{time.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"
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

    def status(self, invoice: str) -> dict[str, object]:
        return self.orders.find(invoice)
