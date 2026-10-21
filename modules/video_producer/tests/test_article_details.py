import unittest

from modules.video_producer.article_details import (
    enrich_articles,
    extract_article_content,
    fetch_article_details,
)


class ArticleDetailsTests(unittest.TestCase):
    def test_extract_article_content_removes_noise_and_keeps_paragraphs(self):
        html = """
        <html><body>
          <script>tracking();</script>
          <style>.ad {}</style>
          <div class="read__content">
            <p>Bournemouth bersiap menjamu AC Milan di fase liga Liga Europa.</p>
            <p>Partai ini penting untuk peluang lolos ke babak sistem gugur.</p>
            <div class="ads">Advertisement</div>
            <p>Ruben Amorim membawa rekor positif ke tanah Inggris.</p>
          </div>
        </body></html>
        """

        result = extract_article_content(html)

        self.assertIn("Bournemouth bersiap menjamu AC Milan", result)
        self.assertIn("peluang lolos", result)
        self.assertIn("Ruben Amorim membawa rekor", result)
        self.assertNotIn("tracking", result)
        self.assertNotIn("Advertisement", result)

    def test_fetch_article_details_uses_html_backend(self):
        class FakeBackend:
            def __init__(self):
                self.urls = []

            def fetch(self, url):
                self.urls.append(url)
                return "<article><p>Isi lengkap berita menjelaskan latar belakang, fakta utama, dan tindak lanjut yang dilakukan.</p></article>"

        backend = FakeBackend()
        article = {"url": "https://example.test/news", "title": "Judul Berita"}

        details = fetch_article_details(article, backend=backend)

        self.assertEqual(backend.urls, ["https://example.test/news"])
        self.assertIn("Isi lengkap berita", details["content"])
        self.assertEqual(details["title"], article["title"])

    def test_enrich_articles_fetches_each_page(self):
        class FakeBackend:
            def __init__(self):
                self.urls = []

            def fetch(self, url):
                self.urls.append(url)
                return f"<article><p>Konten lengkap untuk {url} beserta latar belakang dan tindak lanjutnya.</p></article>"

        articles = [
            {"title": f"Berita {index}", "url": f"https://example.test/{index}"}
            for index in range(1, 4)
        ]
        backend = FakeBackend()

        enriched = enrich_articles(articles, backend=backend)

        self.assertEqual(len(enriched), 3)
        self.assertEqual(backend.urls, [article["url"] for article in articles])
        self.assertTrue(all("Konten lengkap" in article["content"] for article in enriched))
