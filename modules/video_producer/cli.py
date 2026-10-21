import argparse
from datetime import datetime
import os
from pathlib import Path
from typing import Any

import pymysql

from modules.video_producer.article_details import enrich_articles
from modules.telegram_group_reader import load_env_file
from modules.video_producer.article_provider import load_latest_kaltim_articles
from modules.video_producer.producer import build_news_roundup_plan
from modules.video_producer.renderer import render_article_video


DEFAULT_DURATION_SECONDS = 60


def build_roundup_plan(
    articles: list[dict[str, Any]],
    duration_seconds: int = DEFAULT_DURATION_SECONDS,
):
    return build_news_roundup_plan(
        articles,
        duration_seconds=duration_seconds,
    )


def build_default_output_path(articles: list[dict[str, Any]]) -> Path:
    published_at = articles[0].get("published_at")
    if isinstance(published_at, datetime):
        stamp = published_at.strftime("%Y%m%d")
    else:
        stamp = datetime.now().strftime("%Y%m%d")
    return Path("public/generated_video") / f"kaltim_roundup_{stamp}.mp4"


def create_connection() -> pymysql.connections.Connection:
    return pymysql.connect(
        host=os.environ.get("MYSQL_HOST", "127.0.0.1"),
        user=os.environ.get("MYSQL_USER", "root"),
        password=os.environ.get("MYSQL_PASSWORD", ""),
        database=os.environ.get("MYSQL_DATABASE", "telegram_data"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Buat video pembahasan lengkap 3 berita Kaltim")
    parser.add_argument("--output", default="")
    parser.add_argument("--duration", type=int, default=DEFAULT_DURATION_SECONDS)
    parser.add_argument("--fps", type=int, default=24)
    return parser.parse_args()


def main() -> None:
    load_env_file()
    args = parse_args()
    connection = create_connection()
    try:
        articles = load_latest_kaltim_articles(connection, limit=3)
        articles = enrich_articles(articles)
    finally:
        connection.close()

    plan = build_roundup_plan(articles, args.duration)
    output = Path(args.output) if args.output else build_default_output_path(articles)
    result = render_article_video(plan, output, fps=args.fps)
    print(f"Video selesai: {result}")
    print(f"Target pembahasan: {plan.duration_seconds} detik")
    print(f"Voice: {plan.voice}")


if __name__ == "__main__":
    main()
