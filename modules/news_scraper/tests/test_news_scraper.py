import unittest
import ssl
from urllib.error import URLError
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from modules.news_scraper import (
    InMemoryNewsBackend,
    NewsArticle,
    NewsScraper,
    NewsSource,
    HttpNewsBackend,
    parse_rss,
)


SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>Kaltim Feed</title>
  <item>
    <title>Berita hari ini</title>
    <link>https://portal.example/berita-1</link>
    <pubDate>Wed, 21 Oct 2026 08:30:00 +0800</pubDate>
    <description>Ringkasan berita satu.</description>
  </item>
  <item>
    <title>Berita kemarin</title>
    <link>https://portal.example/berita-2</link>
    <pubDate>Tue, 20 Oct 2026 08:30:00 +0800</pubDate>
    <description>Ringkasan berita dua.</description>
  </item>
</channel></rss>"""


class TestParseRss(unittest.TestCase):
    def test_parses_items_into_articles(self) -> None:
        articles = parse_rss(SAMPLE_RSS, source_name="Portal Test")

        self.assertEqual(len(articles), 2)
        self.assertEqual(articles[0].title, "Berita hari ini")
        self.assertEqual(articles[0].url, "https://portal.example/berita-1")
        self.assertEqual(articles[0].source, "Portal Test")
        self.assertEqual(articles[0].published_at.year, 2026)
        self.assertEqual(articles[0].published_at.hour, 8)


class TestNewsScraper(unittest.TestCase):
    def test_portal_sources_cover_kaltim_and_national(self) -> None:
        from modules.news_scraper import PORTAL_SOURCES

        kaltim = [s for s in PORTAL_SOURCES if s.region == "kaltim"]
        national = [s for s in PORTAL_SOURCES if s.region == "nasional"]

        self.assertGreaterEqual(len(kaltim), 4)
        self.assertGreaterEqual(len(national), 6)
        self.assertEqual(len(PORTAL_SOURCES), 12)
        names = {s.name for s in PORTAL_SOURCES}
        self.assertIn("Prokal Kaltim", names)
        self.assertIn("Kaltim Online", names)
        self.assertIn("News Kaltim", names)

    def _backend(self) -> InMemoryNewsBackend:
        return InMemoryNewsBackend(
            feeds={
                "https://a.example/rss": SAMPLE_RSS,
                "https://b.example/rss": SAMPLE_RSS,
            }
        )

    def _sources(self) -> list[NewsSource]:
        return [
            NewsSource(name="Portal A", url="https://a.example/rss", region="kaltim"),
            NewsSource(name="Portal B", url="https://b.example/rss", region="nasional"),
        ]

    def test_scrape_today_filters_only_today_articles(self) -> None:
        scraper = NewsScraper(
            backend=self._backend(),
            sources=self._sources(),
            today=date(2026, 10, 21),
        )

        articles = scraper.scrape_today()

        self.assertEqual(len(articles), 2)
        for article in articles:
            self.assertEqual(article.published_at.date(), date(2026, 10, 21))

    def test_scrape_aggregates_all_sources(self) -> None:
        scraper = NewsScraper(
            backend=self._backend(),
            sources=self._sources(),
            today=date(2026, 10, 21),
        )

        articles = scraper.scrape_today()

        sources = {article.source for article in articles}
        self.assertEqual(sources, {"Portal A", "Portal B"})

    def test_failed_source_does_not_break_scrape(self) -> None:
        backend = InMemoryNewsBackend(feeds={"https://a.example/rss": SAMPLE_RSS})
        sources = [
            NewsSource(name="Portal A", url="https://a.example/rss", region="kaltim"),
            NewsSource(name="Portal Dead", url="https://dead.example/rss", region="kaltim"),
        ]
        scraper = NewsScraper(backend=backend, sources=sources, today=date(2026, 10, 21))

        articles = scraper.scrape_today()

        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].source, "Portal A")

    def test_scrape_errors_are_recorded(self) -> None:
        backend = InMemoryNewsBackend(feeds={"https://a.example/rss": SAMPLE_RSS})
        sources = [
            NewsSource(name="Portal A", url="https://a.example/rss", region="kaltim"),
            NewsSource(name="Portal Dead", url="https://dead.example/rss", region="kaltim"),
        ]
        scraper = NewsScraper(backend=backend, sources=sources, today=date(2026, 10, 21))

        scraper.scrape_today()

        self.assertEqual(len(scraper.errors), 1)
        self.assertEqual(scraper.errors[0][0], "Portal Dead")

    def test_default_today_is_makassar_today(self) -> None:
        scraper = NewsScraper(backend=self._backend(), sources=self._sources())

        expected = datetime.now(ZoneInfo("Asia/Makassar")).date()
        self.assertEqual(scraper.today, expected)


class TestNewsArticle(unittest.TestCase):
    def test_article_holds_fields(self) -> None:
        published = datetime(2026, 10, 21, 8, 30, tzinfo=timezone(timedelta(hours=8)))
        article = NewsArticle(
            source="Portal",
            title="Judul",
            url="https://portal.example/x",
            published_at=published,
            summary="Ringkasan",
            region="kaltim",
        )

        self.assertEqual(article.title, "Judul")
        self.assertEqual(article.region, "kaltim")


class TestHttpNewsBackend(unittest.TestCase):
    def test_retries_with_insecure_context_on_ssl_error(self) -> None:
        backend = HttpNewsBackend()
        calls = []

        def fake_urlopen(request, timeout=0, context=None):
            calls.append(context)
            if len(calls) == 1:
                raise ssl.SSLCertVerificationError("cert expired")
            return FakeResponse("<rss/>")

        original = backend._open
        backend._open = fake_urlopen
        try:
            raw = backend.fetch("https://jpnn.example/rss")
        finally:
            backend._open = original

        self.assertEqual(raw, "<rss/>")
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1].verify_mode, ssl.CERT_NONE)

    def test_retries_when_ssl_error_wrapped_in_urlerror(self) -> None:
        backend = HttpNewsBackend()
        calls = []

        def fake_urlopen(request, timeout=0, context=None):
            calls.append(context)
            if len(calls) == 1:
                raise URLError(ssl.SSLCertVerificationError("cert expired"))
            return FakeResponse("<rss/>")

        original = backend._open
        backend._open = fake_urlopen
        try:
            raw = backend.fetch("https://jpnn.example/rss")
        finally:
            backend._open = original

        self.assertEqual(raw, "<rss/>")
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1].verify_mode, ssl.CERT_NONE)


class FakeResponse:
    def __init__(self, body: str) -> None:
        self._body = body.encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


if __name__ == "__main__":
    unittest.main()
