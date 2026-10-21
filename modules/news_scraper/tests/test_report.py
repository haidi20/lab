import unittest
from datetime import datetime, timezone, timedelta

from modules.news_scraper import NewsArticle
from modules.news_scraper.report import render_markdown


class TestRenderMarkdown(unittest.TestCase):
    def test_renders_articles_grouped_by_source(self) -> None:
        published = datetime(2026, 10, 21, 8, 30, tzinfo=timezone(timedelta(hours=8)))
        articles = [
            NewsArticle("Antara Kaltim", "Judul A", "https://a/1", published, "Ringkasan A", "kaltim"),
            NewsArticle("Antara Kaltim", "Judul B", "https://a/2", published, "Ringkasan B", "kaltim"),
            NewsArticle("Kompas", "Judul C", "https://k/1", published, "Ringkasan C", "nasional"),
        ]

        output = render_markdown(articles, scrape_date=__import__("datetime").date(2026, 10, 21), errors=[])

        self.assertIn("# Berita Hari Ini", output)
        self.assertIn("## Antara Kaltim", output)
        self.assertIn("## Kompas", output)
        self.assertIn("[Judul A](https://a/1)", output)
        self.assertIn("[Judul C](https://k/1)", output)

    def test_renders_errors_section(self) -> None:
        output = render_markdown([], scrape_date=__import__("datetime").date(2026, 10, 21), errors=[("Portal X", "timeout")])

        self.assertIn("Portal X", output)
        self.assertIn("timeout", output)


if __name__ == "__main__":
    unittest.main()
