import json
import tempfile
import unittest
from pathlib import Path

from modules.inaproc.api.auth import AuthError
from modules.inaproc.api.scraper import ScrapeError, TkdnScraper


class FakeLocator:
    def __init__(self, count=1):
        self._count = count

    def count(self):
        return self._count

    @property
    def first(self):
        return self

    def inner_html(self):
        return (
            "<thead><tr><th>Jenis Produk</th><th>Merek</th><th>Tipe</th>"
            "<th>Uraian Produk</th><th>Standard</th><th>Nilai</th></tr></thead>"
            "<tbody><tr><td>Monitor</td><td>acer</td><td>V</td>"
            "<td>23.8 Inchi</td><td>-</td><td>33.39</td></tr></tbody>"
        )


class FakePage:
    def __init__(self, url="https://penyedia.inaproc.id/products/tkdn?keyword=x", rows=1, responses=None):
        self.url = url
        self.rows = rows
        self.goto_url = None
        self.waited = []
        self.responses = list(responses or [])

    def goto(self, url, **kwargs):
        self.goto_url = url
        if self.responses:
            return self.responses.pop(0)
        return None

    def wait_for_selector(self, selector, **kwargs):
        self.waited.append(selector)

    def locator(self, selector):
        if selector == "table tbody tr":
            return FakeLocator(self.rows)
        return FakeLocator(1)


class FakeContext:
    def __init__(self, page):
        self.page = page
        self.state = None

    def new_page(self):
        return self.page

    def close(self):
        pass


class FakeBrowser:
    def __init__(self, context):
        self.context = context
        self.closed = False

    def new_context(self, **kwargs):
        self.state = kwargs.get("storage_state")
        return self.context

    def close(self):
        self.closed = True


class FakePlaywright:
    def __init__(self, browser):
        self.chromium = self
        self.browser = browser

    def launch(self, **kwargs):
        return self.browser


class TkdnScraperTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.session = Path(self.tmp.name) / "storageState.json"
        self.session.write_text(
            json.dumps({"cookies": [{"name": "session"}], "origins": []}),
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def build(self, page):
        browser = FakeBrowser(FakeContext(page))
        return browser, FakePlaywright(browser)

    def test_buka_url_keyword(self):
        page = FakePage()
        browser, pw = self.build(page)
        scraper = TkdnScraper(self.session, playwright=pw)
        scraper.fetch("11469/SJ-IND.8/E-TKDN/7/2025")
        self.assertIn("/products/tkdn?keyword=", page.goto_url)
        self.assertIn("11469%2FSJ-IND.8%2FE-TKDN%2F7%2F2025", page.goto_url)

    def test_pakai_storage_state(self):
        page = FakePage()
        browser, pw = self.build(page)
        TkdnScraper(self.session, playwright=pw).fetch("11469/SJ-IND.8/E-TKDN/7/2025")
        self.assertEqual(browser.state, str(self.session))

    def test_tunggu_tabel_render(self):
        page = FakePage()
        browser, pw = self.build(page)
        TkdnScraper(self.session, playwright=pw).fetch("11469/SJ-IND.8/E-TKDN/7/2025")
        self.assertTrue(page.waited)

    def test_redirect_signin(self):
        page = FakePage(url="https://penyedia.inaproc.id/auth/signin")
        browser, pw = self.build(page)
        with self.assertRaises(AuthError):
            TkdnScraper(self.session, playwright=pw).fetch("11469/SJ-IND.8/E-TKDN/7/2025")

    def test_halaman_kosong(self):
        page = FakePage(rows=0)
        browser, pw = self.build(page)
        result = TkdnScraper(self.session, playwright=pw).fetch(
            "11469/SJ-IND.8/E-TKDN/7/2025"
        )
        self.assertEqual(result.status, "empty")
        self.assertEqual(result.rows, [])

    def test_timeout_selector(self):
        class TimeoutPage(FakePage):
            def wait_for_selector(self, selector, **kwargs):
                raise TimeoutError("selector timeout")

        page = TimeoutPage()
        browser, pw = self.build(page)
        with self.assertRaises(ScrapeError):
            TkdnScraper(self.session, playwright=pw).fetch("11469/SJ-IND.8/E-TKDN/7/2025")

    def test_sesi_hilang(self):
        browser, pw = self.build(FakePage())
        with self.assertRaises(AuthError):
            TkdnScraper(Path(self.tmp.name) / "missing.json", playwright=pw).fetch(
                "11469/SJ-IND.8/E-TKDN/7/2025"
            )

    def test_http_429_dicoba_ulang(self):
        class Response:
            status = 429
            headers = {"retry-after": "0"}

        page = FakePage(responses=[Response()])
        browser, pw = self.build(page)
        sleeps = []
        scraper = TkdnScraper(
            self.session,
            playwright=pw,
            max_retries=1,
            sleep=sleeps.append,
        )
        result = scraper.fetch("11469/SJ-IND.8/E-TKDN/7/2025")
        self.assertEqual(result.status, "found")
        self.assertEqual(len(sleeps), 1)
        self.assertEqual(page.responses, [])


if __name__ == "__main__":
    unittest.main()
