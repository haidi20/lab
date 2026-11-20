import json
import tempfile
import unittest
from pathlib import Path

from modules.inaproc.api.login import login_interaktif


class FakePage:
    def goto(self, url, **kwargs):
        return None

    def wait_for_url(self, pattern, **kwargs):
        return None


class FakeContext:
    def __init__(self, page):
        self.page = page

    def new_page(self):
        return self.page

    def storage_state(self, path=None):
        state = {"cookies": [{"name": "session"}], "origins": []}
        Path(path).write_text(
            json.dumps(state),
            encoding="utf-8",
        )
        return state


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
        self.chromium = self
        self.browser = browser
        self.launch_kwargs = None

    def launch(self, **kwargs):
        self.launch_kwargs = kwargs
        return self.browser


class LoginInteraktifTest(unittest.TestCase):
    def test_login_interaktif_simpan_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            session = Path(tmp) / "storageState.json"
            page = FakePage()
            browser = FakeBrowser(FakeContext(page))
            playwright = FakePlaywright(browser)

            result = login_interaktif(session, playwright=playwright)

            self.assertTrue(session.exists())
            self.assertTrue(result["connected"])
            self.assertEqual(playwright.launch_kwargs["headless"], False)
            self.assertTrue(browser.closed)


if __name__ == "__main__":
    unittest.main()
