from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from modules.inaproc.api.auth import AuthError, muat_storage_state
from modules.inaproc.api.parser import ParserError, parse_rows
from modules.inaproc.api.spt import SptNumber, build_keyword

BASE_URL = "https://penyedia.inaproc.id/products/tkdn"
TABLE_SELECTOR = "table"
ROW_SELECTOR = "table tbody tr"


class ScrapeError(RuntimeError):
    """Raised when the TKDN page cannot be rendered or parsed."""

    def __init__(self, message: str, *, status_code: int | None = None, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after


@dataclass
class ScrapeResult:
    status: str
    rows: list[dict[str, Any]]
    html: str = ""


class TkdnScraper:
    def __init__(
        self,
        session_path: str | Path,
        *,
        playwright=None,
        headless: bool = True,
        timeout_ms: int = 45_000,
        max_retries: int = 2,
        sleep=None,
    ) -> None:
        self.session_path = Path(session_path)
        self._playwright = playwright
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.max_retries = max_retries
        self._sleep = sleep

    def _manager(self):
        if self._playwright is not None:
            return None, self._playwright
        from playwright.sync_api import sync_playwright

        manager = sync_playwright()
        return manager, manager.__enter__()

    def _sleep_backoff(self, attempt: int, retry_after: float | None) -> None:
        if self._sleep is not None:
            self._sleep(retry_after if retry_after is not None else 2 ** attempt)
            return
        import time

        time.sleep(retry_after if retry_after is not None else 2 ** attempt)

    def fetch(self, number: str | SptNumber) -> ScrapeResult:
        spt = number if isinstance(number, SptNumber) else SptNumber.parse(number)
        muat_storage_state(self.session_path)
        attempt = 0
        while True:
            manager, pw = self._manager()
            browser = None
            try:
                browser = pw.chromium.launch(headless=self.headless)
                context = browser.new_context(storage_state=str(self.session_path))
                page = context.new_page()
                response = page.goto(
                    f"{BASE_URL}?keyword={build_keyword(spt)}",
                    wait_until="domcontentloaded",
                )
                status_code = getattr(response, "status", None) if response is not None else None
                if status_code == 429 or (status_code is not None and status_code >= 500):
                    if attempt >= self.max_retries:
                        raise ScrapeError(
                            f"INAPROC page unavailable (HTTP {status_code})",
                            status_code=status_code,
                        )
                    retry_after = None
                    headers = getattr(response, "headers", None) or {}
                    raw_retry = headers.get("retry-after") if hasattr(headers, "get") else None
                    if raw_retry:
                        try:
                            retry_after = float(raw_retry)
                        except (TypeError, ValueError):
                            retry_after = None
                    self._sleep_backoff(attempt, retry_after)
                    attempt += 1
                    continue
                if "/auth/signin" in (page.url or ""):
                    raise AuthError("INAPROC session expired; please reconnect")
                try:
                    page.wait_for_selector(TABLE_SELECTOR, timeout=self.timeout_ms)
                except Exception as exc:
                    raise ScrapeError("TKDN table did not render in time") from exc
                if page.locator(ROW_SELECTOR).count() == 0:
                    return ScrapeResult(status="empty", rows=[])
                table_html = page.locator(TABLE_SELECTOR).first.inner_html()
                html = f"<table>{table_html}</table>"
                try:
                    rows = parse_rows(html)
                except ParserError as exc:
                    raise ScrapeError(str(exc)) from exc
                status = "found" if rows else "empty"
                return ScrapeResult(status=status, rows=rows, html=html)
            except (AuthError, ScrapeError):
                raise
            except Exception as exc:
                raise ScrapeError("Failed to open the INAPROC TKDN page") from exc
            finally:
                if browser is not None:
                    browser.close()
                if manager is not None:
                    manager.__exit__(None, None, None)