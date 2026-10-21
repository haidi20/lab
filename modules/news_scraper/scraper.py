import xml.etree.ElementTree as ET
import ssl
from urllib.error import URLError
from dataclasses import dataclass, field
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


MAKASSAR = ZoneInfo("Asia/Makassar")


@dataclass(frozen=True)
class NewsSource:
    name: str
    url: str
    region: str


@dataclass(frozen=True)
class NewsArticle:
    source: str
    title: str
    url: str
    published_at: datetime | None = None
    summary: str = ""
    region: str = ""


@dataclass
class ScrapeResult:
    articles: list[NewsArticle] = field(default_factory=list)
    errors: list[tuple[str, str]] = field(default_factory=list)


PORTAL_SOURCES: list[NewsSource] = [
    NewsSource("Antara Kaltim", "https://kaltim.antaranews.com/rss/terkini.xml", "kaltim"),
    NewsSource("Tribun Kaltim", "https://kaltim.tribunnews.com/rss", "kaltim"),
    NewsSource("Prokal Kaltim", "https://prokal.co/rss/kaltim", "kaltim"),
    NewsSource("Kaltim Online", "https://kaltimonline.com/feed", "kaltim"),
    NewsSource("News Kaltim", "https://newskaltim.com/feed", "kaltim"),
    NewsSource("Antara Nasional", "https://www.antaranews.com/rss/terkini.xml", "nasional"),
    NewsSource("Tribunnews", "https://www.tribunnews.com/rss", "nasional"),
    NewsSource("Media Indonesia", "https://mediaindonesia.com/rss", "nasional"),
    NewsSource("JPNN", "https://www.jpnn.com/rss", "nasional"),
    NewsSource("CNBC Indonesia", "https://www.cnbcindonesia.com/rss", "nasional"),
    NewsSource("Republika", "https://www.republika.co.id/rss", "nasional"),
    NewsSource("CNN Indonesia", "https://www.cnnindonesia.com/rss", "nasional"),
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _parse_pub_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        pass
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def parse_rss(raw_xml: str, source_name: str, region: str = "") -> list[NewsArticle]:
    root = ET.fromstring(raw_xml)
    articles: list[NewsArticle] = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        if not title or not link:
            continue
        articles.append(
            NewsArticle(
                source=source_name,
                title=title,
                url=link,
                published_at=_parse_pub_date(item.findtext("pubDate")),
                summary=(item.findtext("description") or "").strip(),
                region=region,
            )
        )
    return articles


class InMemoryNewsBackend:
    def __init__(self, feeds: dict[str, str]) -> None:
        self._feeds = feeds

    def fetch(self, url: str) -> str:
        feed = self._feeds.get(url)
        if feed is None:
            raise ValueError(f"No feed configured for {url}")
        return feed


class HttpNewsBackend:
    def __init__(self, timeout_seconds: int = 20) -> None:
        self._timeout = timeout_seconds

    def _open(self, request: Request, context: ssl.SSLContext | None = None):
        return urlopen(request, timeout=self._timeout, context=context)

    def fetch(self, url: str) -> str:
        request = Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with self._open(request) as response:
                return response.read().decode("utf-8", errors="replace")
        except (ssl.SSLError, URLError) as exc:
            reason = getattr(exc, "reason", None)
            if isinstance(exc, URLError) and not isinstance(reason, ssl.SSLError):
                raise
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            with self._open(request, context=context) as response:
                return response.read().decode("utf-8", errors="replace")


class NewsScraper:
    def __init__(
        self,
        backend: Any,
        sources: list[NewsSource] | None = None,
        today: date | None = None,
    ) -> None:
        self._backend = backend
        self._sources = sources if sources is not None else PORTAL_SOURCES
        self.today = today if today is not None else datetime.now(MAKASSAR).date()
        self.errors: list[tuple[str, str]] = []

    def scrape_today(self) -> list[NewsArticle]:
        self.errors = []
        articles: list[NewsArticle] = []
        for source in self._sources:
            try:
                raw = self._backend.fetch(source.url)
                parsed = parse_rss(raw, source_name=source.name, region=source.region)
                articles.extend(a for a in parsed if self._is_today(a))
            except Exception as exc:
                self.errors.append((source.name, str(exc)))
        return articles

    def _is_today(self, article: NewsArticle) -> bool:
        if article.published_at is None:
            return False
        published = article.published_at
        if published.tzinfo is not None:
            published = published.astimezone(MAKASSAR)
        return published.date() == self.today
