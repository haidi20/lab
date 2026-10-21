from __future__ import annotations

import hashlib
import json
import urllib.request
from typing import Callable

Transport = Callable[[str, str, dict[str, object]], dict[str, object]]


class DigiflazzClient:
    def __init__(
        self,
        username: str,
        api_key: str,
        base_url: str = "https://api.digiflazz.com",
        transport: Transport | None = None,
    ) -> None:
        self.username = username
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.transport = transport or self._http_transport

    @staticmethod
    def _http_transport(method: str, url: str, payload: dict[str, object]) -> dict[str, object]:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method=method,
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def _sign(self, action: str) -> str:
        return hashlib.md5(f"{self.username}{self.api_key}{action}".encode()).hexdigest()

    def balance(self) -> int:
        response = self.transport(
            "POST",
            f"{self.base_url}/v1/cek-saldo",
            {"cmd": "deposit", "username": self.username, "sign": self._sign("deposit")},
        )
        data = response.get("data", {})
        return int(data.get("deposit", 0)) if isinstance(data, dict) else 0

    def price_list(self, code: str | None = None) -> list[dict[str, object]]:
        payload: dict[str, object] = {
            "cmd": "price",
            "username": self.username,
            "sign": self._sign("pricetype"),
        }
        if code:
            payload["code"] = code
        response = self.transport("POST", f"{self.base_url}/v1/price-list", payload)
        data = response.get("data", [])
        return data if isinstance(data, list) else []

    def create_transaction(
        self,
        buyer_sku_code: str,
        customer_no: str,
        ref_id: str,
        testing: bool = False,
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "username": self.username,
            "buyer_sku_code": buyer_sku_code,
            "customer_no": customer_no,
            "ref_id": ref_id,
            "sign": self._sign(ref_id),
        }
        if testing:
            payload["testing"] = True
        response = self.transport("POST", f"{self.base_url}/v1/transaction", payload)
        data = response.get("data", response)
        return data if isinstance(data, dict) else dict(response)
