from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_MYSQL_HOST = "127.0.0.1"
DEFAULT_MYSQL_PORT = 3306
DEFAULT_MYSQL_USER = "root"


class InaprocConfigError(RuntimeError):
    """Raised when required INAPROC configuration is missing or invalid."""


def load_env_file(path: Path | str = Path(".env")) -> None:
    """Load simple KEY=VALUE pairs without overriding existing environment."""
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip('"').strip("'")


def _read_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise InaprocConfigError(f"{name} must be an integer, got {raw!r}") from exc


@dataclass(frozen=True)
class InaprocDbConfig:
    host: str
    port: int
    user: str
    database: str
    password: str = field(default="", repr=False)
    connect_timeout: int = 10

    @classmethod
    def from_env(cls) -> "InaprocDbConfig":
        database = os.environ.get("INAPROC_MYSQL_DATABASE", "").strip()
        if not database:
            raise InaprocConfigError(
                "INAPROC_MYSQL_DATABASE is required; it does not fall back to MYSQL_DATABASE"
            )
        return cls(
            host=os.environ.get("INAPROC_MYSQL_HOST", "").strip()
            or os.environ.get("MYSQL_HOST", "").strip()
            or DEFAULT_MYSQL_HOST,
            port=_read_int(
                "INAPROC_MYSQL_PORT",
                _read_int("MYSQL_PORT", DEFAULT_MYSQL_PORT),
            ),
            user=os.environ.get("INAPROC_MYSQL_USER", "").strip()
            or os.environ.get("MYSQL_USER", "").strip()
            or DEFAULT_MYSQL_USER,
            password=os.environ.get("INAPROC_MYSQL_PASSWORD")
            if "INAPROC_MYSQL_PASSWORD" in os.environ
            else os.environ.get("MYSQL_PASSWORD", ""),
            database=database,
            connect_timeout=_read_int("INAPROC_MYSQL_CONNECT_TIMEOUT", 10),
        )


@dataclass(frozen=True)
class GatewayConfig:
    base_url: str
    token: str = field(default="", repr=False)
    timeout: int = 30
    max_retries: int = 3
    enabled: bool = False

    @classmethod
    def from_env(cls) -> "GatewayConfig":
        token = os.environ.get("INAPROC_API_TOKEN", "").strip()
        enabled = os.environ.get("INAPROC_API_ENABLED", "false").strip().lower() in {
            "1",
            "true",
            "yes",
        }
        return cls(
            base_url=os.environ.get(
                "INAPROC_API_BASE_URL", "https://data.inaproc.id"
            ).rstrip("/"),
            token=token,
            timeout=_read_int("INAPROC_API_TIMEOUT", 30),
            max_retries=_read_int("INAPROC_API_MAX_RETRIES", 3),
            enabled=enabled and bool(token),
        )
