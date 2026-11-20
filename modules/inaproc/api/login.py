from __future__ import annotations

from pathlib import Path
from typing import Any

from modules.inaproc.api.auth import SIGNIN_URL, AuthError, validasi_sesi


def login_interaktif(
    session_path: str | Path,
    *,
    playwright=None,
    timeout_ms: int = 300_000,
) -> dict[str, Any]:
    """Fallback for OTP/captcha: the operator finishes login in a visible browser."""
    session = Path(session_path)
    session.parent.mkdir(parents=True, exist_ok=True)
    manager = None
    pw = playwright
    if pw is None:
        from playwright.sync_api import sync_playwright

        manager = sync_playwright()
        pw = manager.__enter__()
    browser = None
    try:
        browser = pw.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(SIGNIN_URL, wait_until="domcontentloaded")
        page.wait_for_url("**/products/tkdn**", timeout=timeout_ms)
        state = context.storage_state(path=str(session))
        validasi_sesi(state)
    except AuthError:
        raise
    except Exception as exc:
        raise AuthError("Interactive INAPROC login did not complete") from exc
    finally:
        if browser is not None:
            browser.close()
        if manager is not None:
            manager.__exit__(None, None, None)
    return {"connected": True, "session_path": str(session)}
