from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from .bot import TelegramStoreBot, load_env_file
from .client import DigiflazzClient
from .service import TelegramStoreService


class UnconfiguredDigiflazzClient:
    def price_list(self, code: str | None = None) -> list[dict[str, object]]:
        return []

    def create_transaction(self, buyer_sku_code: str, customer_no: str, ref_id: str, testing: bool = False) -> dict[str, object]:
        raise ValueError("Kredensial Digiflazz belum diisi")

    def balance(self) -> int:
        return 0


def build_bot_from_env(
    env_path: str | Path = ".env",
    send_message: Callable[[int, str], None] | None = None,
    api_base_url: str = "https://api.telegram.org",
) -> TelegramStoreBot:
    load_env_file(env_path)
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    digiflazz_username = os.environ.get("DIGIFLAZZ_USERNAME", "")
    digiflazz_api_key = os.environ.get("DIGIFLAZZ_API_KEY", "")
    if not token:
        raise RuntimeError("Environment belum lengkap: TELEGRAM_BOT_TOKEN")

    if digiflazz_username and digiflazz_api_key:
        digiflazz = DigiflazzClient(digiflazz_username, digiflazz_api_key)
    else:
        digiflazz = UnconfiguredDigiflazzClient()
    service = TelegramStoreService(
        digiflazz,
        markup_percent=float(os.environ.get("STORE_MARKUP_PERCENT", "0")),
        testing=os.environ.get("DIGIFLAZZ_TESTING", "false").lower() == "true",
    )
    return TelegramStoreBot(
        token,
        service,
        bot_username=os.environ.get("TELEGRAM_BOT_USERNAME", "@hn_assistent_bot"),
        send_message=send_message,
        api_base_url=api_base_url,
    )


def main() -> None:
    build_bot_from_env().run()


if __name__ == "__main__":
    main()
