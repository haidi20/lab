import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from modules.telegram_group_reader.reader import TelegramGroupReader


def load_env_file(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def default_since(days: int = 10) -> datetime:
    return datetime.now(ZoneInfo("Asia/Makassar")) - timedelta(days=days)


@dataclass(frozen=True)
class SyncConfig:
    api_id: int
    api_hash: str
    session: str
    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_database: str

    @classmethod
    def from_env(cls) -> "SyncConfig":
        return cls(
            api_id=int(os.environ.get("TELEGRAM_API_ID", "0")),
            api_hash=os.environ.get("TELEGRAM_API_HASH", ""),
            session=os.environ.get("TELEGRAM_SESSION", "telegram_group_reader"),
            mysql_host=os.environ.get("MYSQL_HOST", "127.0.0.1"),
            mysql_port=int(os.environ.get("MYSQL_PORT", "3306")),
            mysql_user=os.environ.get("MYSQL_USER", "root"),
            mysql_password=os.environ.get("MYSQL_PASSWORD", ""),
            mysql_database=os.environ.get("MYSQL_DATABASE", "telegram_data"),
        )


def run_sync(reader: TelegramGroupReader, store, since: datetime | None = None) -> dict[str, int]:
    groups = reader.get_all_groups()
    store.save_groups(groups)

    total_messages = 0
    all_messages = reader.get_all_messages_from_all_groups(since=since)
    for group_title, messages in all_messages.items():
        store.save_messages(group_title, messages)
        total_messages += len(messages)

    return {"groups": len(groups), "messages": total_messages}
