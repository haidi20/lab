from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SIGNIN_URL = "https://penyedia.inaproc.id/auth/signin?callbackUrl=/products/tkdn"
TKDN_URL = "https://penyedia.inaproc.id/products/tkdn"

NOT_REGISTERED_MARKERS = (
    "tidak terdaftar",
    "belum terdaftar",
    "email not registered",
    "account not found",
)


class AuthError(RuntimeError):
    """Raised when the INAPROC provider session cannot be established or loaded."""


def validasi_sesi(state: Any) -> bool:
    if not isinstance(state, dict):
        raise AuthError("INAPROC session state must be a JSON object")
    cookies = state.get("cookies")
    origins = state.get("origins")
    if cookies is None or origins is None:
        raise AuthError("INAPROC session state must contain cookies and origins")
    if not isinstance(cookies, list) or not isinstance(origins, list):
        raise AuthError("INAPROC session state has invalid cookies/origins")
    has_cookie = any(isinstance(c, dict) and c.get("name") for c in cookies)
    has_storage = any(
        isinstance(o, dict) and o.get("localStorage") for o in origins
    )
    if not has_cookie and not has_storage:
        raise AuthError("INAPROC session state has no cookies or localStorage")
    return True


def muat_storage_state(path: str | Path) -> dict[str, Any]:
    session_path = Path(path)
    if not session_path.exists():
        raise AuthError(f"INAPROC session file not found: {session_path}")
    try:
        state = json.loads(session_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuthError(f"INAPROC session file is not valid JSON: {session_path}") from exc
    validasi_sesi(state)
    return state


def _playwright_manager(playwright):
    if playwright is not None:
        return None, playwright
    from playwright.sync_api import sync_playwright

    manager = sync_playwright()
    return manager, manager.__enter__()


def connect_inaproc(
    email: str,
    password: str,
    session_path: str | Path,
    *,
    playwright=None,
    headless: bool = True,
) -> dict[str, Any]:
    """Open an INAPROC provider session once and persist storageState.json."""
    if not email or not password:
        raise AuthError("INAPROC email and password are required")

    session = Path(session_path)
    session.parent.mkdir(parents=True, exist_ok=True)
    manager, pw = _playwright_manager(playwright)
    browser = None
    try:
        browser = pw.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        page.goto(SIGNIN_URL, wait_until="domcontentloaded")
        page.fill("input[type=email]", email)
        page.fill("input[type=password]", password)
        page.click("button[type=submit]")
        try:
            page.wait_for_url("**/products/tkdn**", timeout=45_000)
        except Exception as exc:
            if _email_not_registered(page):
                raise AuthError("INAPROC email is not registered") from exc
            raise
        state = context.storage_state(path=str(session))
        validasi_sesi(state)
    except AuthError:
        raise
    except Exception as exc:
        raise AuthError(
            "Could not connect to INAPROC; check credentials or use the interactive login"
        ) from exc
    finally:
        if browser is not None:
            browser.close()
        if manager is not None:
            manager.__exit__(None, None, None)

    logger.info("INAPROC provider session saved to %s", session)
    return {"connected": True, "session_path": str(session)}


def _email_not_registered(page) -> bool:
    try:
        text = page.inner_text("body").lower()
    except Exception:
        return False
    return any(marker in text for marker in NOT_REGISTERED_MARKERS)
