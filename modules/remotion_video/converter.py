from __future__ import annotations

from typing import Any, Mapping

from modules.ui_animation.producer import VideoPlan


def articles_to_cover_props(
    articles: list[Mapping[str, Any]],
) -> dict[str, object]:
    if len(articles) != 3:
        raise ValueError("Cover membutuhkan tepat 3 artikel")

    return {
        "width": 1080,
        "height": 1350,
        "title": "3 Berita Terbaru Kaltim",
        "articles": [
            {
                "index": index,
                "title": str(article.get("title", "")).strip(),
                "source": str(article.get("source", "")).strip(),
            }
            for index, article in enumerate(articles, start=1)
        ],
    }


def plan_to_remotion_props(
    plan: VideoPlan,
    fps: int = 24,
    audio_directory: str = "audio",
) -> dict[str, object]:
    scenes = []
    for scene in plan.scenes:
        duration_in_frames = max(1, round(scene.duration * fps))
        scenes.append(
            {
                "index": scene.index,
                "startFrame": sum(
                    max(1, round(item.duration * fps)) for item in plan.scenes[: scene.index - 1]
                ),
                "durationInFrames": duration_in_frames,
                "heading": scene.heading,
                "title": scene.title or plan.title,
                "caption": scene.caption,
                "narration": scene.narration,
                "layout": scene.layout,
                "source": scene.source or plan.source,
                "hook": scene.hook,
                "audioPath": f"{audio_directory}/scene_{scene.index:02d}.mp3",
            }
        )

    return {
        "width": 1080,
        "height": 1920,
        "fps": fps,
        "title": plan.title,
        "source": plan.source,
        "voice": plan.voice,
        "durationInFrames": sum(scene["durationInFrames"] for scene in scenes),
        "scenes": scenes,
    }
