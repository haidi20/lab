from __future__ import annotations

import os
import shutil
import json
import subprocess
import urllib.request
from pathlib import Path
from typing import Callable

from .bot import TelegramStoreBot, load_env_file
from .client import DigiflazzClient
from .hermes_status import HermesStatusProvider
from .hermes_chat import HermesChatClient
from .service import TelegramStoreService
from .catalog import SQLiteProductCatalog
from .store import SQLiteOrderStore

TRELLO_PROGRESS_LIST_ID = "6ad7fee5455f933ec728788c"
_WINDOWS_HIDE_FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
_HERMES_HIDDEN_WRAPPER = Path(__file__).with_name("bin") / "hermes-hidden.cmd"


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
    digiflazz_development_key = os.environ.get("DIGIFLAZZ_DEVELOPMENT_KEY", "")
    if not token:
        raise RuntimeError("Environment belum lengkap: TELEGRAM_BOT_TOKEN")

    if digiflazz_username and digiflazz_api_key:
        digiflazz = DigiflazzClient(
            digiflazz_username,
            digiflazz_api_key,
            development_key=digiflazz_development_key or digiflazz_api_key,
        )
    else:
        digiflazz = UnconfiguredDigiflazzClient()
    service = TelegramStoreService(
        digiflazz,
        markup_percent=float(os.environ.get("STORE_MARKUP_PERCENT", "0")),
        testing=os.environ.get("DIGIFLAZZ_TESTING", "false").lower() == "true",
        catalog=SQLiteProductCatalog(os.environ.get("PRODUCT_CATALOG_PATH", "modules/telegram_store/data/products.sqlite3")),
    )
    service.testing = os.environ.get("DIGIFLAZZ_TESTING", "false").lower() == "true"
    update_store = SQLiteOrderStore(os.environ.get("TELEGRAM_STORE_STATE_PATH", "modules/telegram_store/data/store.sqlite3"))
    service.orders = update_store
    webhook_key = os.environ.get("DIGIFLAZZ_WEBHOOK_API_KEY", "")
    if not webhook_key:
        webhook_key = digiflazz_development_key if service.testing else digiflazz_api_key
    service.digiflazz_api_key = webhook_key
    trello_key = os.environ.get("TRELLO_API_KEY", "")
    trello_token = os.environ.get("TRELLO_TOKEN", "")
    hermes_status: HermesStatusProvider | None = None
    if trello_key and trello_token:
        hermes_home = Path(os.environ.get("HERMES_HOME", str(Path.home() / "AppData" / "Local" / "hermes")))
        hermes_status = HermesStatusProvider(
            trello_fetch=_fetch_trello,
            trello_key=trello_key,
            trello_token=trello_token,
            progress_list_id=os.environ.get("TRELLO_PROGRESS_LIST_ID", TRELLO_PROGRESS_LIST_ID),
            jobs_path=hermes_home / "cron" / "jobs.json",
            delegation_root=hermes_home / "cache" / "delegation" / "live",
            agent_log_path=hermes_home / "logs" / "agent.log",
        )
    hermes_binary = os.environ.get("HERMES_BIN")
    if not hermes_binary:
        hermes_binary = (
            str(_HERMES_HIDDEN_WRAPPER)
            if _HERMES_HIDDEN_WRAPPER.exists()
            else shutil.which("hermes") or "hermes"
        )
    hermes_workdir = Path(os.environ.get("HERMES_WORKDIR", "D:/projects/klinik-git"))
    provider_base_url = os.environ.get("HERMES_PROVIDER_BASE_URL", "")
    provider_api_key = os.environ.get("HERMES_PROVIDER_API_KEY", "")
    provider_model = os.environ.get("HERMES_PROVIDER_MODEL", "cd")
    provider_post = (
        _post_provider
        if provider_base_url and provider_api_key
        else None
    )
    fallback_providers = _fallback_providers_from_env()
    hermes_chat = HermesChatClient(
        runner=_run_hermes_command,
        hermes_binary=hermes_binary,
        workdir=hermes_workdir,
        status_provider=hermes_status,
        timeout=float(os.environ.get("HERMES_CHAT_TIMEOUT_SECONDS", "900")),
        provider_post=provider_post,
        provider_model=provider_model,
        fallback_providers=fallback_providers,
    )
    if digiflazz_username and digiflazz_api_key:
        digiflazz.set_mode("sandbox" if service.testing else "prod")
    return TelegramStoreBot(
        token,
        service,
        bot_username=os.environ.get("TELEGRAM_BOT_USERNAME", "@hn_assistent_bot"),
        send_message=send_message,
        api_base_url=api_base_url,
        hermes_status=hermes_status,
        hermes_chat=hermes_chat,
        live_interval=float(os.environ.get("HERMES_LIVE_INTERVAL_SECONDS", "5")),
        live_duration_seconds=float(os.environ.get("HERMES_LIVE_DURATION_SECONDS", "60")),
        deposit_owner_name=os.environ.get("DIGIFLAZZ_OWNER_NAME", ""),
        update_offset_store=update_store,
        mode="sandbox" if service.testing else "prod",
    )


def _fetch_trello(url: str) -> object:
    with urllib.request.urlopen(url, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def _run_hermes_command(command: list[str], input_bytes: bytes, timeout: float) -> object:
    return subprocess.run(
        command,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout + 10,
        cwd=str(Path(os.environ.get("HERMES_WORKDIR", "D:/projects/klinik-git"))),
        check=False,
        creationflags=_WINDOWS_HIDE_FLAGS,
    )


def _post_provider(payload: dict[str, object]) -> object:
    base_url = os.environ.get("HERMES_PROVIDER_BASE_URL", "").rstrip("/")
    api_key = os.environ.get("HERMES_PROVIDER_API_KEY", "")
    timeout = float(os.environ.get("HERMES_CHAT_TIMEOUT_SECONDS", "900"))
    request = urllib.request.Request(
        f"{base_url}/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    build_bot_from_env().run()


if __name__ == "__main__":
    main()

def _fallback_providers_from_env() -> list[dict[str, object]]:
    providers: list[dict[str, object]] = []
    definitions = [
        ("limo_router", "LIMO_ROUTER"),
        ("nilovr", "NILOVR"),
        ("nocta", "NOCTA"),
        ("mahi_center", "MAHI_CENTER"),
        ("tip_router", "TIP_ROUTER"),
        ("mazov", "MAZOV"),
    ]
    for name, prefix in definitions:
        base_url = os.environ.get(f"{prefix}_BASE_URL", "").strip()
        api_key = os.environ.get(f"{prefix}_API_KEY", "").strip()
        model = os.environ.get(f"{prefix}_MODEL", "").strip()
        if base_url and api_key and model:
            providers.append(
                {
                    "name": name,
                    "base_url": base_url,
                    "api_key": api_key,
                    "model": model,
                    "post": _post_fallback_provider,
                }
            )
    return providers

def _post_fallback_provider(payload: dict[str, object]) -> object:
    provider = payload.pop("provider", {})
    assert isinstance(provider, dict)
    base_url = str(provider.get("base_url", "")).rstrip("/")
    api_key = str(provider.get("api_key", ""))
    timeout = float(os.environ.get("HERMES_CHAT_TIMEOUT_SECONDS", "900"))
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))
