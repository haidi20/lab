from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from modules.video_producer.producer import adjust_plan_to_audio, VideoPlan
from .converter import plan_to_remotion_props


def build_remotion_payload(
    plan: VideoPlan,
    audio_durations: list[float],
    fps: int = 24,
) -> tuple[VideoPlan, dict[str, object]]:
    synced_plan = adjust_plan_to_audio(plan, audio_durations)
    props = plan_to_remotion_props(synced_plan, fps=fps)
    return synced_plan, props


def build_render_command(
    props_path: str | Path,
    output_path: str | Path,
) -> list[str]:
    executable = resolve_executable("bunx")
    return [
        executable,
        "remotion",
        "render",
        "KaltimRoundup",
        str(Path(output_path).resolve()),
        f"--props={Path(props_path).resolve()}",
        "--port=3100",
    ]


def resolve_executable(name: str) -> str:
    executable = shutil.which(name)
    if not executable:
        raise RuntimeError(f"Executable tidak ditemukan: {name}")
    return executable


def _ffmpeg_executable() -> str:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        found = shutil.which("ffmpeg")
        if not found:
            raise RuntimeError("ffmpeg tidak ditemukan; install imageio-ffmpeg")
        return found


def audio_duration(audio_path: str | Path) -> float:
    ffmpeg = _ffmpeg_executable()
    result = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", str(audio_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", result.stderr)
    if not match:
        raise RuntimeError(f"Tidak bisa membaca durasi audio: {audio_path}")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def prepare_remotion_project(
    plan: VideoPlan,
    audio_paths: list[Path],
    audio_durations: list[float],
    build_dir: Path,
    project_dir: Path,
    fps: int = 24,
) -> Path:
    if len(audio_paths) != len(plan.scenes):
        raise ValueError("Jumlah audio tidak sama dengan jumlah scene")

    synced_plan, props = build_remotion_payload(plan, audio_durations, fps=fps)
    audio_output = project_dir / "public" / "audio"
    audio_output.mkdir(parents=True, exist_ok=True)
    for audio_path in audio_paths:
        shutil.copy2(audio_path, audio_output / audio_path.name)

    build_dir.mkdir(parents=True, exist_ok=True)
    props_path = build_dir / "props.json"
    props_path.write_text(json.dumps(props, ensure_ascii=False, indent=2), encoding="utf-8")
    return props_path
