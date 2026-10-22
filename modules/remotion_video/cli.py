from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import pymysql

from modules.remotion_video.pipeline import (
    audio_duration,
    build_render_command,
    prepare_remotion_project,
)
from modules.telegram_group_reader import load_env_file
from modules.ui_animation.article_details import enrich_articles
from modules.ui_animation.article_provider import load_latest_kaltim_articles
from modules.ui_animation.producer import build_news_roundup_plan
from modules.ui_animation.renderer import EdgeTTSEngine


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
    return Path("public/generated_video") / f"kaltim_remotion_{stamp}.mp4"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render video Kaltim dengan Remotion")
    parser.add_argument("--output", default="")
    parser.add_argument("--fps", type=int, default=24)
    return parser.parse_args()


def main() -> None:
    load_env_file()
    args = parse_args()
    connection = create_connection()
    try:
        articles = enrich_articles(load_latest_kaltim_articles(connection, limit=3))
    finally:
        connection.close()

    plan = build_news_roundup_plan(articles, duration_seconds=180)
    output = Path(args.output) if args.output else default_output()
    build_dir = output.parent / f"{output.stem}_remotion_build"
    build_dir.mkdir(parents=True, exist_ok=True)
    project_dir = Path(__file__).parent / "remotion"

    engine = EdgeTTSEngine()
    audio_paths = []
    for scene in plan.scenes:
        audio_path = build_dir / f"scene_{scene.index:02d}.mp3"
        engine.synthesize(scene.narration, audio_path, plan.voice)
        audio_paths.append(audio_path)

    durations = [audio_duration(audio_path) for audio_path in audio_paths]
    props_path = prepare_remotion_project(
        plan,
        audio_paths=audio_paths,
        audio_durations=durations,
        build_dir=build_dir,
        project_dir=project_dir,
        fps=args.fps,
    )
    command = build_render_command(props_path, output)
    subprocess_run(command, cwd=project_dir)
    print(f"Video selesai: {output.resolve()}")
    print(f"Props: {props_path.resolve()}")


def subprocess_run(command: list[str], cwd: Path) -> None:
    import subprocess

    subprocess.run(command, check=True, cwd=cwd)


if __name__ == "__main__":
    main()
