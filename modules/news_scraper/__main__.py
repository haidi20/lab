from datetime import datetime
from pathlib import Path

import pymysql

from modules.news_scraper import HttpNewsBackend, NewsMysqlStore, NewsScraper
from modules.news_scraper.report import render_markdown
from modules.telegram_group_reader import load_env_file
import os


def main() -> None:
    load_env_file()
    scraper = NewsScraper(backend=HttpNewsBackend())
    articles = scraper.scrape_today()

    conn = pymysql.connect(
        host=os.environ.get("MYSQL_HOST", "127.0.0.1"),
        user=os.environ.get("MYSQL_USER", "root"),
        password=os.environ.get("MYSQL_PASSWORD", ""),
        database=os.environ.get("MYSQL_DATABASE", "telegram_data"),
        charset="utf8mb4",
    )
    store = NewsMysqlStore(conn)
    store.save_articles(articles)
    conn.close()

    output = render_markdown(articles, scrape_date=scraper.today, errors=scraper.errors)
    target = Path("news_today.md")
    target.write_text(output, encoding="utf-8")

    print(f"Scrape selesai: {len(articles)} artikel hari ini dari {len(scraper._sources)} portal.")
    print(f"Upsert ke DB: {len(articles)} artikel (tabel news_articles).")
    if scraper.errors:
        print(f"Portal gagal: {len(scraper.errors)}")
    print(f"Hasil ditulis ke {target.resolve()}")


if __name__ == "__main__":
    main()
