from dataclasses import dataclass
import html
import re
import textwrap
from typing import Mapping, Sequence


MALE_INDONESIAN_VOICE = "id-ID-ArdiNeural"


@dataclass(frozen=True)
class Scene:
    index: int
    start: float
    end: float
    duration: float
    heading: str
    narration: str
    caption: str
    layout: str = "headline"
    title: str = ""
    source: str = ""
    hook: str = ""


@dataclass(frozen=True)
class VideoPlan:
    title: str
    source: str
    url: str
    duration_seconds: float
    voice: str
    narration: str
    scenes: tuple[Scene, ...]


def html_to_text(raw: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", html.unescape(raw))
    return " ".join(without_tags.split())


def layout_text(text: str, max_characters: int = 24) -> list[str]:
    return textwrap.wrap(
        text,
        width=max_characters,
        break_long_words=False,
        break_on_hyphens=False,
    )


def _sentences(text: str, limit: int = 3) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [part.strip() for part in parts if part.strip()][:limit]


def build_video_plan(
    article: Mapping[str, str],
    narration_points: Sequence[str] | None = None,
    conclusion: str = "",
    duration_seconds: float = 30,
    voice: str = MALE_INDONESIAN_VOICE,
) -> VideoPlan:
    title = html_to_text(str(article["title"]))
    source = html_to_text(str(article.get("source", "Sumber berita")))
    url = str(article.get("url", ""))
    summary = html_to_text(str(article.get("summary", "")))
    points = list(narration_points or _sentences(summary))
    final_conclusion = conclusion or (points[-1] if points else title)
    hook = "Tiga kabar Kaltim hari ini bisa mengubah rencanamu."

    scene_narrations = [
        f"Berita Kaltim hari ini: {title}.",
        points[0] if len(points) > 0 else summary,
        points[1] if len(points) > 1 else summary,
        f"{final_conclusion} Sumber: {source}.",
    ]

    headings = ["Berita Utama", "Temuan", "Langkah Pemerintah", "Kesimpulan"]
    layouts = ["headline", "metrics", "process", "conclusion"]
    scene_duration = duration_seconds / len(scene_narrations)
    scenes = []
    for index, narration in enumerate(scene_narrations):
        start = index * scene_duration
        end = start + scene_duration
        scenes.append(
            Scene(
                index=index + 1,
                start=start,
                end=end,
                duration=scene_duration,
                heading=headings[index],
                narration=narration,
                caption=narration,
                layout=layouts[index],
                title=title,
                source=source,
                hook=hook if index == 0 else "",
            )
        )

    return VideoPlan(
        title=title,
        source=source,
        url=url,
        duration_seconds=duration_seconds,
        voice=voice,
        narration=" ".join(scene_narrations),
        scenes=tuple(scenes),
    )


def _compact_text(text: str, max_characters: int = 125) -> str:
    compact = html_to_text(text)
    if len(compact) <= max_characters:
        return compact
    return textwrap.shorten(compact, width=max_characters, placeholder="...")


def _detailed_text(text: str, max_characters: int = 500) -> str:
    compact = html_to_text(text)
    if len(compact) <= max_characters:
        return compact
    sentences = re.split(r"(?<=[.!?])\s+", compact)
    result = ""
    for sentence in sentences:
        candidate = f"{result} {sentence}".strip()
        if len(candidate) > max_characters:
            break
        result = candidate
    if result:
        return result
    return textwrap.shorten(compact, width=max_characters, placeholder="...")


def build_news_roundup_plan(
    articles: Sequence[Mapping[str, str]],
    duration_seconds: float = 60,
    voice: str = MALE_INDONESIAN_VOICE,
) -> VideoPlan:
    if len(articles) != 3:
        raise ValueError("Format roundup membutuhkan tepat 3 artikel Kaltim")

    cleaned = []
    for article in articles:
        cleaned.append(
            {
                "title": html_to_text(str(article["title"])),
                "summary": html_to_text(str(article.get("summary", ""))),
                "content": html_to_text(str(article.get("content", article.get("summary", "")))),
                "source": html_to_text(str(article.get("source", "Sumber berita"))),
                "url": str(article.get("url", "")),
            }
        )

    hook = "Tiga kabar Kaltim hari ini bisa mengubah rencanamu."

    short_mode = duration_seconds <= 90
    intro_limit = 115 if short_mode else 240
    detail_limit = 165 if short_mode else 500
    article_intros = [
        f"Pembahasan pertama kita mulai dari konteksnya. {_detailed_text(cleaned[0]['content'], intro_limit)}",
        f"Pembahasan kedua dimulai dari latar belakangnya. {_detailed_text(cleaned[1]['content'], intro_limit)}",
        f"Pembahasan ketiga berfokus pada situasinya. {_detailed_text(cleaned[2]['content'], intro_limit)}",
    ]
    article_details = [
        f"Kita masuk ke pembahasan lengkapnya. {_detailed_text(cleaned[0]['content'], detail_limit)}",
        f"Sekarang kita uraikan fakta dan dampaknya. {_detailed_text(cleaned[1]['content'], detail_limit)}",
        f"Bagian ini menjelaskan kronologi dan tindak lanjutnya. {_detailed_text(cleaned[2]['content'], detail_limit)}",
    ]
    conclusion = (
        "Kesimpulan dari tiga berita Kaltim hari ini: ketiganya menunjukkan dinamika yang perlu diikuti "
        "karena berdampak langsung pada masyarakat, baik dari sisi mobilitas, layanan publik, maupun "
        "kegiatan ekonomi dan olahraga. Informasi utamanya mencakup latar belakang, fakta lapangan, "
        "dampak langsung, serta arah tindak lanjut dari pihak terkait. Pantau perkembangan berikutnya "
        "melalui sumber resmi, evaluasi kebijakan terbaru, dan informasi operasional agar tidak salah "
        "memahami situasi."
    )
    if short_mode:
        conclusion = (
            "Kesimpulan tiga berita Kaltim: kondisinya berdampak langsung pada mobilitas, layanan publik, "
            "dan ekonomi warga. Tindak lanjutnya adalah pemantauan berkala, koordinasi instansi, dan "
            "pembaruan informasi resmi."
        )
    narrations = []
    for index in range(3):
        narrations.append(article_intros[index])
        narrations.append(article_details[index])
    narrations.append(conclusion)
    headings = [
        "Berita 1/3",
        "Pembahasan 1/3",
        "Berita 2/3",
        "Pembahasan 2/3",
        "Berita 3/3",
        "Pembahasan 3/3",
        "Ringkasan",
    ]
    layouts = [
        "headline",
        "detail",
        "metrics",
        "detail",
        "process",
        "detail",
        "conclusion",
    ]
    scene_duration = duration_seconds / len(narrations)
    scenes = []
    for index, narration in enumerate(narrations):
        if index == 0:
            narration = f"{hook} {narration}"
        start = index * scene_duration
        article_index = index // 2
        scenes.append(
            Scene(
                index=index + 1,
                start=start,
                end=start + scene_duration,
                duration=scene_duration,
                heading=headings[index],
                narration=narration,
                caption=narration,
                layout=layouts[index],
                title=cleaned[article_index]["title"] if index < 6 else "Ringkasan Kaltim",
                source=cleaned[article_index]["source"] if index < 6 else "Kaltim",
                hook=hook if index == 0 else "",
            )
        )

    return VideoPlan(
        title=cleaned[0]["title"],
        source=", ".join(dict.fromkeys(article["source"] for article in cleaned)),
        url=cleaned[0]["url"],
        duration_seconds=duration_seconds,
        voice=voice,
        narration=" ".join(narrations),
        scenes=tuple(scenes),
    )

def build_single_news_plan(
    article: Mapping[str, str],
    duration_seconds: float = 60,
    voice: str = MALE_INDONESIAN_VOICE,
) -> VideoPlan:
    cleaned = {
        "title": html_to_text(str(article["title"])),
        "summary": html_to_text(str(article.get("summary", ""))),
        "content": html_to_text(str(article.get("content", article.get("summary", "")))),
        "source": html_to_text(str(article.get("source", "Sumber berita"))),
        "url": str(article.get("url", "")),
    }
    hook = "Satu perubahan Kaltim berdampak langsung pada hari ini."
    context = _detailed_text(cleaned["content"], 190)
    detail = _detailed_text(cleaned["content"], 240)
    closing = _detailed_text(cleaned["content"], 190)
    narrations = [
        f"{hook} Konteksnya, {context}",
        f"Fakta dan dampaknya, {detail}",
        f"Tindak lanjutnya, {closing}",
    ]
    headings = ["Konteks", "Fakta & Dampak", "Tindak Lanjut"]
    layouts = ["headline", "detail", "conclusion"]
    scene_duration = duration_seconds / len(narrations)
    scenes = []
    for index, narration in enumerate(narrations):
        start = index * scene_duration
        scenes.append(
            Scene(
                index=index + 1,
                start=start,
                end=start + scene_duration,
                duration=scene_duration,
                heading=headings[index],
                narration=narration,
                caption=narration,
                layout=layouts[index],
                title=cleaned["title"],
                source=cleaned["source"],
                hook=hook if index == 0 else "",
            )
        )

    return VideoPlan(
        title=cleaned["title"],
        source=cleaned["source"],
        url=cleaned["url"],
        duration_seconds=duration_seconds,
        voice=voice,
        narration=" ".join(narrations),
        scenes=tuple(scenes),
    )


def adjust_plan_to_audio(
    plan: VideoPlan,
    audio_durations: Sequence[float],
    tail_seconds: float = 0.35,
) -> VideoPlan:
    if len(audio_durations) != len(plan.scenes):
        raise ValueError("Jumlah durasi audio tidak sama dengan jumlah scene")

    scenes = []
    current_time = 0.0
    for scene, audio_duration in zip(plan.scenes, audio_durations):
        duration = max(float(audio_duration) + tail_seconds, 2.5)
        scenes.append(
            Scene(
                index=scene.index,
                start=current_time,
                end=current_time + duration,
                duration=duration,
                heading=scene.heading,
                narration=scene.narration,
                caption=scene.caption,
                layout=scene.layout,
                title=scene.title,
                source=scene.source,
                hook=scene.hook,
            )
        )
        current_time += duration

    return VideoPlan(
        title=plan.title,
        source=plan.source,
        url=plan.url,
        duration_seconds=current_time,
        voice=plan.voice,
        narration=plan.narration,
        scenes=tuple(scenes),
    )


def build_ffmpeg_scene_args(
    frame_pattern: str,
    audio_path: str,
    output_path: str,
    duration: float,
    fps: int = 30,
) -> list[str]:
    duration_text = str(duration)
    return [
        "ffmpeg",
        "-y",
        "-framerate",
        str(fps),
        "-i",
        frame_pattern,
        "-i",
        audio_path,
        "-filter_complex",
        f"[1:a]apad=whole_dur={duration_text}[a]",
        "-map",
        "0:v",
        "-map",
        "[a]",
        "-t",
        duration_text,
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-ar",
        "44100",
        "-ac",
        "2",
        output_path,
    ]


def build_concat_args(
    concat_list_path: str,
    output_path: str,
) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        concat_list_path,
        "-c",
        "copy",
        output_path,
    ]
