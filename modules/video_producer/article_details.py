from typing import Any

import requests
from bs4 import BeautifulSoup


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class HttpArticleBackend:
    def __init__(self, timeout_seconds: int = 20) -> None:
        self._timeout = timeout_seconds

    def fetch(self, url: str) -> str:
        response = requests.get(
            url,
            timeout=self._timeout,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
        return response.text


def _clean_text(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def extract_article_content(html: str, max_paragraphs: int = 8) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for selector in ("script", "style", "aside", "figure", "figcaption", "nav", "footer"):
        for element in soup.select(selector):
            element.decompose()

    containers = soup.select(
        ", ".join(
            [
                ".read__content",
                ".article-content",
                ".article__body",
                ".detail__body-text",
                ".post-content",
                ".entry-content",
                "article",
                "main",
                "body",
            ]
        )
    )
    for container in containers:
        paragraphs = []
        for paragraph in container.find_all("p"):
            text = _clean_text(paragraph.get_text(" ", strip=True))
            if len(text) < 45:
                continue
            lowered = text.lower()
            noise_markers = (
                "advertisement",
                "baca juga",
                "simpan artikel",
                "ikuti kami",
                "dilarang keras mengambil konten",
                "copyright",
                "pewarta:",
            )
            if any(marker in lowered for marker in noise_markers):
                continue
            if text not in paragraphs:
                paragraphs.append(text)
        if paragraphs:
            return " ".join(paragraphs[:max_paragraphs])
    return ""


def fetch_article_details(
    article: dict[str, Any],
    backend: Any | None = None,
    max_paragraphs: int = 8,
) -> dict[str, Any]:
    selected_backend = backend or HttpArticleBackend()
    html = selected_backend.fetch(str(article["url"]))
    details = dict(article)
    details["content"] = extract_article_content(html, max_paragraphs=max_paragraphs)
    return details


def enrich_articles(
    articles: list[dict[str, Any]],
    backend: Any | None = None,
    max_paragraphs: int = 8,
) -> list[dict[str, Any]]:
    selected_backend = backend or HttpArticleBackend()
    return [
        fetch_article_details(
            article,
            backend=selected_backend,
            max_paragraphs=max_paragraphs,
        )
        for article in articles
    ]
