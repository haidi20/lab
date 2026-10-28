from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path

import pymysql

from modules.telegram_group_reader import load_env_file
from modules.remotion_video.converter import articles_to_cover_props
from modules.remotion_video.pipeline import build_still_command
from modules.ui_animation.article_provider import load_latest_kaltim_articles


def create_connection() -> pymysql.connections.Connection:
    import os

    return pymysql.connect(
        host=os.environ.get("MYSQL_HOST", "127.0.0.1"),
        user=os.environ.get("MYSQL_USER", "root"),
        password=os.environ.get("MYSQL_PASSWORD", ""),
        database=os.environ.get("MYSQL_DATABASE", "telegram_data"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def default_output() -> Path:
    stamp = datetime.now().strftime("%Y%m%d")
    return Path("public/generated_images") / f"kaltim_cover_{stamp}.png"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render cover Kaltim dengan Remotion")
    parser.add_argument("--output", default="")
    return parser.parse_args()


def main() -> None:
    load_env_file()
    args = parse_args()
    connection = create_connection()
    try:
        articles = load_latest_kaltim_articles(connection, limit=3, today_only=False)
    finally:
        connection.close()

    props = articles_to_cover_props(articles)
    output = Path(args.output) if args.output else default_output()
    build_dir = output.parent / f"{output.stem}_build"
    build_dir.mkdir(parents=True, exist_ok=True)
    props_path = build_dir / "cover.json"
    props_path.write_text(json.dumps(props, ensure_ascii=False, indent=2), encoding="utf-8")

    project_dir = Path(__file__).parent / "remotion"
    subprocess.run(
        build_still_command(props_path, output),
        check=True,
        cwd=project_dir,
    )
    print(f"Gambar selesai: {output.resolve()}")


if __name__ == "__main__":
    main()
