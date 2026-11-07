from __future__ import annotations

import json
import sqlite3
from pathlib import Path


class SQLiteProductCatalog:
    def __init__(self, path: str | Path, ttl_seconds: int = 300) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds
        self.connection = sqlite3.connect(str(self.path), check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                buyer_sku_code TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at INTEGER NOT NULL
            )
            """
        )
        self.connection.commit()

    def replace_all(self, products: list[dict[str, object]]) -> None:
        import time
        now = int(time.time())
        with self.connection:
            self.connection.execute("DELETE FROM products")
            for product in products:
                self.connection.execute(
                    "INSERT OR REPLACE INTO products(buyer_sku_code, payload, updated_at) VALUES (?, ?, ?)",
                    (str(product.get("buyer_sku_code", "")), json.dumps(product, sort_keys=True), now),
                )

    def get_all(self) -> list[dict[str, object]]:
        rows = self.connection.execute("SELECT payload FROM products ORDER BY buyer_sku_code").fetchall()
        return [dict(json.loads(row["payload"])) for row in rows]
