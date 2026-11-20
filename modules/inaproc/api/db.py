from __future__ import annotations

from typing import Any, Callable

import pymysql
import pymysql.cursors

from modules.inaproc.api.config import InaprocDbConfig


class DbUnavailableError(RuntimeError):
    """Raised when MySQL cannot be reached; maps to HTTP 503 db_unavailable."""

    code = "db_unavailable"

    def __init__(self, message: str = "MySQL is unavailable") -> None:
        super().__init__(f"db_unavailable: {message}")


def connect_mysql(config: InaprocDbConfig, connect_timeout: int | None = None):
    """Open a MySQL connection with utf8mb4 and DictCursor."""
    try:
        return pymysql.connect(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=config.database,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=connect_timeout or config.connect_timeout,
            autocommit=False,
        )
    except (pymysql.err.OperationalError, pymysql.err.InterfaceError) as exc:
        raise DbUnavailableError(
            f"cannot connect to {config.host}:{config.port}/{config.database}"
        ) from exc


ConnectionFactory = Callable[[], Any]
