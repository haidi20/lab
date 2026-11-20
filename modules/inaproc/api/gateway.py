from __future__ import annotations

import logging
import random
import time
from typing import Any, Callable, Iterator, Mapping

import httpx

from modules.inaproc.api.config import GatewayConfig

logger = logging.getLogger(__name__)

class GatewayError(RuntimeError):
    """Base error for INAPROC API Gateway integration."""

class GatewayClientError(GatewayError):
    """Raised for non-retryable API errors."""

class GatewayAuthError(GatewayClientError):
    """Raised for 401/403 responses; the token is invalid or expired."""

class GatewayDisabledError(GatewayAuthError):
    """Raised when the Gateway token is missing or disabled."""

def redact_token(text: str, token: str) -> str:
    if not token:
        return text
    return str(text).replace(token, "***")

class InaprocGatewayClient:
    """GET-only client for the official INAPROC API Gateway."""

    def __init__(
        self,
        config: GatewayConfig,
        *,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        jitter: Callable[[float, float], float] = random.uniform,
        on_retry: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.config = config
        self.enabled = bool(config.enabled and config.token)
        self._sleep = sleep
        self._jitter = jitter
        self._on_retry = on_retry
        self._client = httpx.Client(
            base_url=config.base_url,
            timeout=config.timeout,
            transport=transport,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {config.token}" if config.token else "",
            },
        )

    def set_retry_callback(
        self, callback: Callable[[dict[str, Any]], None] | None
    ) -> None:
        self._on_retry = callback

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "InaprocGatewayClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def get(self, path: str, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
        if not self.config.token or not self.config.enabled:
            raise GatewayDisabledError("INAPROC API Gateway is disabled or has no token")
        attempt = 0
        while True:
            try:
                response = self._client.get(path, params=dict(params or {}))
            except httpx.HTTPError as exc:
                if attempt >= self.config.max_retries:
                    raise GatewayClientError(
                        redact_token(f"INAPROC Gateway request failed: {exc}", self.config.token)
                    ) from exc
                self._notify_retry(path, attempt, None, None)
                self._backoff(attempt, None)
                attempt += 1
                continue

            if response.status_code == 200:
                try:
                    return response.json()
                except ValueError as exc:
                    raise GatewayClientError("INAPROC Gateway returned invalid JSON") from exc

            if response.status_code in {401, 403}:
                raise GatewayAuthError(
                    f"INAPROC Gateway rejected the token (HTTP {response.status_code})"
                )

            if response.status_code == 429 or response.status_code >= 500:
                if attempt >= self.config.max_retries:
                    raise GatewayClientError(
                        f"INAPROC Gateway unavailable (HTTP {response.status_code})"
                    )
                retry_after = _parse_retry_after(response.headers.get("retry-after"))
                self._notify_retry(path, attempt, response.status_code, retry_after)
                self._backoff(attempt, retry_after)
                attempt += 1
                continue

            detail = redact_token(_short_body(response), self.config.token)
            raise GatewayClientError(
                f"INAPROC Gateway error (HTTP {response.status_code}): {detail}"
            )

    def paginate(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        limit: int = 100,
        cursor: str | None = None,
        max_pages: int = 10_000,
        on_cursor: Callable[[str | None], None] | None = None,
    ) -> Iterator[list[dict[str, Any]]]:
        base_params = dict(params or {})
        base_params["limit"] = limit
        current = cursor
        for _ in range(max_pages):
            query = dict(base_params)
            if current:
                query["cursor"] = current
            payload = self.get(path, query)
            page = [row for row in (payload.get("data") or []) if isinstance(row, dict)]
            if on_cursor is not None:
                on_cursor(current)
            if page:
                yield page
            meta = payload.get("meta") or {}
            if not meta.get("has_more"):
                return
            next_cursor = meta.get("cursor")
            if not next_cursor or next_cursor == current:
                return
            current = next_cursor

    def _notify_retry(
        self,
        path: str,
        attempt: int,
        status_code: int | None,
        retry_after: float | None,
    ) -> None:
        if self._on_retry is None:
            return
        self._on_retry(
            {
                "path": path,
                "attempt": attempt + 1,
                "status_code": status_code,
                "retry_after": retry_after,
            }
        )

    def _backoff(self, attempt: int, retry_after: float | None) -> None:
        if retry_after is not None:
            delay = max(0.0, retry_after)
        else:
            delay = min(30.0, (2 ** attempt) + self._jitter(0.0, 0.5))
        logger.info("INAPROC Gateway retry in %.2fs (attempt %d)", delay, attempt + 1)
        self._sleep(delay)

def _parse_retry_after(raw: str | None) -> float | None:
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None

def _short_body(response: httpx.Response) -> str:
    text = response.text or ""
    return text[:300]
