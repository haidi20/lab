from datetime import date, datetime
from typing import Any

from modules.news_scraper.scraper import NewsArticle


class NewsMysqlStore:
    def __init__(self, connection: Any) -> None:
        self._connection = connection
        self._create_schema()

    def _create_schema(self) -> None:
        cursor = self._connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS news_articles (
                url VARCHAR(512) PRIMARY KEY,
                title VARCHAR(512) NOT NULL,
                source VARCHAR(100) NOT NULL,
                region VARCHAR(50) NOT NULL DEFAULT '',
                summary TEXT,
                published_at DATETIME NULL,
                published_date DATE GENERATED ALWAYS AS (DATE(published_at)) STORED,
                INDEX idx_source (source),
                INDEX idx_published_date (published_date)
            )
            """
        )
        self._connection.commit()

    def save_articles(self, articles: list[NewsArticle]) -> None:
        if not articles:
            return
        cursor = self._connection.cursor()
        cursor.executemany(
            """
            INSERT INTO news_articles (url, title, source, region, summary, published_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                summary = VALUES(summary),
                published_at = VALUES(published_at)
            """,
            [
                (
                    article.url,
                    article.title,
                    article.source,
                    article.region,
                    article.summary,
                    article.published_at,
                )
                for article in articles
            ],
        )
        self._connection.commit()

    def load_articles(self, on_date: date | None = None) -> list[NewsArticle]:
        cursor = self._connection.cursor()
        if on_date is None:
            cursor.execute(
                "SELECT url, title, source, region, summary, published_at "
                "FROM news_articles ORDER BY published_at DESC"
            )
            params: tuple = ()
        else:
            cursor.execute(
                "SELECT url, title, source, region, summary, published_at "
                "FROM news_articles WHERE published_date = %s "
                "ORDER BY published_at DESC",
                (on_date,),
            )
            params = (on_date,)
        return [
            NewsArticle(
                source=row[2],
                title=row[1],
                url=row[0],
                published_at=row[5],
                summary=row[4] or "",
                region=row[3],
            )
            for row in cursor.fetchall()
        ]
