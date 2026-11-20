import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from modules.inaproc.api.auth import (
    AuthError,
    connect_inaproc,
    muat_storage_state,
    validasi_sesi,
)


class FakePage:
    def __init__(self, fail_on=None, body_text=""):
        self.fail_on = fail_on
        self.filled = {}
        self.clicked = False
        self.body_text = body_text

    def goto(self, url, **kwargs):
        if self.fail_on == "goto":
            raise TimeoutError("navigation timeout")

    def fill(self, selector, value):
        self.filled[selector] = value

    def click(self, selector):
        self.clicked = True
        if self.fail_on == "click":
            raise TimeoutError("submit timeout")

    def wait_for_url(self, pattern, **kwargs):
        if self.fail_on == "wait":
            raise TimeoutError("redirect timeout")

    def inner_text(self, selector):
        return self.body_text


class FakeContext:
    def __init__(self, page, fail_state=False):
        self.page = page
        self.fail_state = fail_state
        self.saved_path = None

    def new_page(self):
        return self.page

    def storage_state(self, path=None):
        if self.fail_state:
            raise RuntimeError("cannot save state")
        self.saved_path = path
        Path(path).write_text(
            json.dumps({"cookies": [{"name": "session"}], "origins": []}),
            encoding="utf-8",
        )
        return {"cookies": [{"name": "session"}], "origins": []}

    def close(self):
        pass


class FakeBrowser:
    def __init__(self, context):
        self.context = context
        self.closed = False

    def new_context(self, **kwargs):
        return self.context

    def close(self):
        self.closed = True


class FakePlaywright:
    def __init__(self, browser):
        self.chromium = MagicMock()
        self.chromium.launch.return_value = browser


class AuthStateTest(unittest.TestCase):
    def test_state_valid(self):
        state = {
            "cookies": [{"name": "session", "value": "x"}],
            "origins": [],
        }
        self.assertTrue(validasi_sesi(state))

    def test_state_dengan_localstorage_diterima(self):
        state = {
            "cookies": [],
            "origins": [
                {
                    "origin": "https://penyedia.inaproc.id",
                    "localStorage": [{"name": "token", "value": "x"}],
                }
            ],
        }
        self.assertTrue(validasi_sesi(state))

    def test_state_tanpa_cookie(self):
        with self.assertRaises(AuthError):
            validasi_sesi({"cookies": [], "origins": []})

    def test_state_tidak_valid(self):
        with self.assertRaises(AuthError) as ctx:
            validasi_sesi(["not", "a", "dict"])
        self.assertIn("session", str(ctx.exception).lower())

    def test_state_hilang(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.json"
            with self.assertRaises(AuthError):
                muat_storage_state(missing)


class ConnectInaprocTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.session_path = Path(self.tmp.name) / "storageState.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_connect_inaproc_simpan_state(self):
        page = FakePage()
        context = FakeContext(page)
        browser = FakeBrowser(context)
        playwright = FakePlaywright(browser)

        result = connect_inaproc(
            "user@example.com",
            "secret",
            self.session_path,
            playwright=playwright,
        )

        self.assertTrue(self.session_path.exists())
        self.assertTrue(result["connected"])
        self.assertEqual(page.filled["input[type=email]"], "user@example.com")
        self.assertTrue(page.clicked)
        self.assertTrue(browser.closed)

    def test_connect_inaproc_kredensial_salah(self):
        page = FakePage(fail_on="wait")
        context = FakeContext(page)
        browser = FakeBrowser(context)
        playwright = FakePlaywright(browser)

        with self.assertRaises(AuthError):
            connect_inaproc(
                "user@example.com",
                "wrong",
                self.session_path,
                playwright=playwright,
            )
        self.assertFalse(self.session_path.exists())

    def test_connect_inaproc_email_tidak_terdaftar(self):
        page = FakePage(fail_on="wait", body_text="Email tidak terdaftar")
        context = FakeContext(page)
        browser = FakeBrowser(context)
        playwright = FakePlaywright(browser)

        with self.assertRaises(AuthError) as ctx:
            connect_inaproc(
                "unknown@example.com",
                "secret",
                self.session_path,
                playwright=playwright,
            )

        self.assertIn("not registered", str(ctx.exception).lower())
        self.assertFalse(self.session_path.exists())
        self.assertTrue(browser.closed)

    def test_connect_inaproc_timeout(self):
        page = FakePage(fail_on="goto")
        context = FakeContext(page)
        browser = FakeBrowser(context)
        playwright = FakePlaywright(browser)

        with self.assertRaises(AuthError):
            connect_inaproc(
                "user@example.com",
                "secret",
                self.session_path,
                playwright=playwright,
            )
        self.assertFalse(self.session_path.exists())

    def test_password_tidak_dilog(self):
        page = FakePage()
        context = FakeContext(page)
        browser = FakeBrowser(context)
        playwright = FakePlaywright(browser)

        with self.assertLogs("modules.inaproc.api.auth", level="INFO") as logs:
            connect_inaproc(
                "user@example.com",
                "super-secret-password",
                self.session_path,
                playwright=playwright,
            )

        joined = "\n".join(logs.output)
        self.assertNotIn("super-secret-password", joined)


if __name__ == "__main__":
    unittest.main()
