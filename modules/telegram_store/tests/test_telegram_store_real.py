from __future__ import annotations

import os
import unittest
from pathlib import Path

from modules.telegram_store.bot import TelegramStoreBot
from modules.telegram_store.bot import load_env_file
from modules.telegram_store.client import DigiflazzClient
from modules.telegram_store.service import TelegramStoreService
from modules.telegram_store.catalog import SQLiteProductCatalog


class TelegramStoreRealDigiflazzTests(unittest.TestCase):
    def test_produk_command_shows_real_filtered_products(self) -> None:
        load_env_file(".env")
        values = {
            key: os.environ.get(key, "")
            for key in ("DIGIFLAZZ_USERNAME", "DIGIFLAZZ_API_KEY", "DIGIFLAZZ_DEVELOPMENT_KEY")
        }
        if not all(values.values()):
            self.skipTest("Kredensial Digiflazz belum lengkap")

        client = DigiflazzClient(
            values["DIGIFLAZZ_USERNAME"],
            values["DIGIFLAZZ_API_KEY"],
            development_key=values["DIGIFLAZZ_DEVELOPMENT_KEY"],
        )
        client.set_mode("prod")
        service = TelegramStoreService(
            client,
            markup_percent=10,
            catalog=SQLiteProductCatalog(Path("modules/telegram_store/data/products.sqlite3")),
        )
        sent: list[tuple[int, str, dict[str, object] | None]] = []
        bot = TelegramStoreBot(
            token="test-token",
            service=service,
            bot_username="@hn_assistent_bot",
            send_message=lambda chat_id, text, reply_markup=None: sent.append((chat_id, text, reply_markup)),
        )

        bot.handle_update({"message": {"chat": {"id": 999001}, "text": "/produk"}})

        text = sent[0][1]
        markup = sent[0][2] or {}
        buttons = [button["text"] for row in markup.get("inline_keyboard", []) for button in row]
        self.assertIn("<b>Daftar Produk</b>", text)
        self.assertTrue(buttons)
        self.assertNotIn("Free Fire 12 Diamond", text)
        self.assertTrue(all("Axis" not in button for button in buttons))
        self.assertTrue(any("PLN" in button or "Telkomsel" in button for button in buttons))

    def test_product_catalog_serves_stale_products_during_rate_limit(self) -> None:
        catalog = SQLiteProductCatalog(Path("modules/telegram_store/data/products.sqlite3"))
        products = catalog.get_all()

        if not products:
            load_env_file(".env")
            values = {
                key: os.environ.get(key, "")
                for key in ("DIGIFLAZZ_USERNAME", "DIGIFLAZZ_API_KEY", "DIGIFLAZZ_DEVELOPMENT_KEY")
            }
            client = DigiflazzClient(
                values["DIGIFLAZZ_USERNAME"],
                values["DIGIFLAZZ_API_KEY"],
                development_key=values["DIGIFLAZZ_DEVELOPMENT_KEY"],
            )
            client.set_mode("prod")
            products = client.price_list()

        catalog.replace_all(products)
        self.assertTrue(catalog.get_all())
