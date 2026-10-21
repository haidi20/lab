import asyncio
import math
from pathlib import Path
import re
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageFont

from modules.video_producer.producer import (
    Scene,
    VideoPlan,
    adjust_plan_to_audio,
    build_concat_args,
    build_ffmpeg_scene_args,
    layout_text,
)


BACKGROUND_TOP = (250, 252, 255)
BACKGROUND_BOTTOM = (209, 229, 255)
CARD_COLOR = (255, 255, 255)
INK_COLOR = (15, 23, 42)
MUTED_COLOR = (100, 116, 139)
BLUE_COLOR = (37, 99, 235)
SOFT_BLUE = (96, 165, 250)
PALE_BLUE = (191, 219, 254)
MOTION_TOKENS = {
    "ease_out_strong": (0.23, 1.0, 0.32, 1.0),
    "ease_in_out_strong": (0.77, 0.0, 0.175, 1.0),
    "enter_duration_seconds": 0.2,
    "on_screen_duration_seconds": 0.35,
    "stagger_seconds": 0.05,
}


class EdgeTTSEngine:
    def synthesize(self, text: str, output_path: Path, voice: str) -> None:
        import edge_tts

        async def generate() -> None:
            communicate = edge_tts.Communicate(text, voice, rate="+0%", pitch="+0Hz")
            await communicate.save(str(output_path))

        asyncio.run(generate())


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in ("arialbd.ttf", "segoeuib.ttf", "arial.ttf"):
        path = Path("C:/Windows/Fonts") / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def ease_out_cubic(value: float) -> float:
    normalized = _clamp(value)
    return 1 - (1 - normalized) ** 3

def _bezier_component(time: float, first: float, second: float) -> float:
    inverse = 1 - time
    return (
        3 * inverse * inverse * time * first
        + 3 * inverse * time * time * second
        + time ** 3
    )

def _cubic_bezier(value: float, curve: tuple[float, float, float, float]) -> float:
    if value <= 0.0:
        return 0.0
    if value >= 1.0:
        return 1.0
    low, high = 0.0, 1.0
    for _ in range(28):
        midpoint = (low + high) / 2
        if _bezier_component(midpoint, curve[0], curve[2]) < value:
            low = midpoint
        else:
            high = midpoint
    time = (low + high) / 2
    return _bezier_component(time, curve[1], curve[3])

def ease_out_strong(value: float) -> float:
    return _cubic_bezier(_clamp(value), MOTION_TOKENS["ease_out_strong"])

def ease_in_out_strong(value: float) -> float:
    return _cubic_bezier(_clamp(value), MOTION_TOKENS["ease_in_out_strong"])

def stagger_step(scene_duration: float) -> float:
    if scene_duration <= 0:
        return 0.0
    return MOTION_TOKENS["stagger_seconds"] / scene_duration


def _mix_color(
    first: tuple[int, int, int],
    second: tuple[int, int, int],
    ratio: float,
) -> tuple[int, int, int]:
    return tuple(
        round(first[position] + (second[position] - first[position]) * ratio)
        for position in range(3)
    )


def _local_progress(scene: Scene, progress: float, total_duration: float) -> float:
    global_time = _clamp(progress) * total_duration
    return _clamp((global_time - scene.start) / max(scene.duration, 0.001))

def _layout_motion(layout: str, progress: float) -> tuple[float, float, float, float]:
    phase = math.tau * _clamp(progress)
    wave = math.sin(phase)
    cosine = math.cos(phase)
    motions = {
        "headline": (18.0 * wave, 14.0 * cosine, 1.035 + 0.015 * cosine, 1.25 + 0.05 * wave),
        "detail": (-24.0 * wave, 18.0 * math.sin(phase + 0.7), 1.045 + 0.020 * wave, 1.25 + 0.05 * wave),
        "metrics": (26.0 * cosine + 8.0, -14.0 * wave, 1.038 + 0.018 * wave, 1.25 + 0.05 * cosine),
        "process": (-20.0 * cosine + 10.0, 22.0 * math.sin(phase + 1.1) + 18.0, 1.045 + 0.022 * cosine, 1.25 + 0.05 * wave),
        "conclusion": (22.0 * math.cos(phase + 0.4), -20.0 * wave, 1.040 + 0.020 * wave, 1.25 + 0.05 * cosine),
    }
    return motions.get(layout, (14.0 * wave, 10.0 * cosine, 1.025 + 0.012 * cosine, 1.2 * wave))

def _layout_motif_motion(layout: str, progress: float) -> tuple[float, float, float, float]:
    phase = math.tau * _clamp(progress)
    wave = math.sin(phase)
    cosine = math.cos(phase)
    motifs = {
        "headline": (0.08 + 0.16 * cosine, 0.12 + 0.08 * wave, 12.0 * wave, 1.02 + 0.02 * cosine),
        "detail": (0.22 + 0.10 * wave, 0.36 + 0.18 * cosine, -14.0 * cosine, 1.03 + 0.03 * wave),
        "metrics": (0.18 + 0.22 * cosine, 0.58 + 0.10 * wave, 18.0 * cosine, 1.02 + 0.025 * wave),
        "process": (0.34 + 0.14 * wave, 0.70 + 0.16 * cosine, -20.0 * wave, 1.04 + 0.03 * cosine),
        "conclusion": (0.66 + 0.18 * cosine, 0.30 + 0.20 * wave, 24.0 * cosine, 1.03 + 0.025 * wave),
    }
    return motifs.get(layout, (0.5 + 0.1 * wave, 0.5 + 0.1 * cosine, 10.0 * wave, 1.02 + 0.02 * cosine))

def _draw_layout_motif(
    layer: Image.Image,
    layout: str,
    progress: float,
    width: int,
    height: int,
) -> None:
    draw = ImageDraw.Draw(layer)
    offset_x_ratio, offset_y_ratio, rotation, scale = _layout_motif_motion(layout, progress)
    center_x = width * offset_x_ratio
    center_y = height * offset_y_ratio

    if layout == "headline":
        for index in range(5):
            bar_width = round(width * (0.55 + index * 0.08) * scale)
            y = center_y + index * 44
            x = center_x - bar_width / 2 + 40 * math.sin(math.tau * progress + index)
            draw.rounded_rectangle(
                (x, y, x + bar_width, y + 14),
                radius=7,
                fill=(255, 255, 255, 54),
            )
    elif layout == "detail":
        for index in range(7):
            dot_y = center_y + index * 38 + 16 * math.sin(math.tau * progress + index * 0.6)
            radius = 7 + 3 * math.sin(math.tau * progress * 1.7 + index)
            draw.ellipse(
                (center_x - radius, dot_y - radius, center_x + radius, dot_y + radius),
                fill=SOFT_BLUE + (68,),
            )
    elif layout == "metrics":
        for index in range(6):
            bar_height = round(34 + 32 * abs(math.sin(math.tau * progress * (0.8 + index * 0.12))))
            x = center_x + index * 62
            draw.rounded_rectangle(
                (x, center_y - bar_height, x + 26, center_y),
                radius=12,
                fill=(255, 255, 255, 62),
            )
    elif layout == "process":
        for index in range(4):
            chevron_x = center_x + index * 58 + 34 * math.sin(math.tau * progress + index * 0.8)
            chevron_y = center_y + index * 18
            draw.line(
                (chevron_x, chevron_y, chevron_x + 28, chevron_y + 24),
                fill=SOFT_BLUE + (74,),
                width=9,
            )
            draw.line(
                (chevron_x + 28, chevron_y + 24, chevron_x, chevron_y + 48),
                fill=SOFT_BLUE + (74,),
                width=9,
            )
    else:
        for index in range(3):
            radius = (86 + index * 42) * scale
            start = math.degrees(math.tau * progress * (0.55 + index * 0.18) + index)
            draw.arc(
                (center_x - radius, center_y - radius, center_x + radius, center_y + radius),
                start=start,
                end=start + 115,
                fill=SOFT_BLUE + (72,),
                width=8,
            )

def _animate_layer(layer: Image.Image, motion: tuple[float, float, float, float]) -> Image.Image:
    width, height = layer.size
    center_x, center_y = width / 2, height / 2
    offset_x, offset_y, scale, rotation = motion
    angle = math.radians(rotation)
    cosine = math.cos(angle) * scale
    sine = math.sin(angle) * scale
    matrix = (
        cosine,
        sine,
        center_x - cosine * center_x - sine * center_y + offset_x,
        -sine,
        cosine,
        center_y - sine * center_x - cosine * center_y + offset_y,
    )
    return layer.transform(
        layer.size,
        Image.AFFINE,
        matrix,
        resample=Image.Resampling.BICUBIC,
        fillcolor=(0, 0, 0, 0),
    )


def _background(
    size: tuple[int, int],
    progress: float,
    settle: float,
    variant: int = 0,
) -> Image.Image:
    width, height = size
    gradient = Image.new("RGB", (1, height))
    for y in range(height):
        ratio = y / height
        base = _mix_color(BACKGROUND_TOP, BACKGROUND_BOTTOM, ratio)
        wave = round(5 * math.sin(math.tau * (ratio * 0.55 + progress * 0.75)))
        gradient.putpixel(
            (0, y),
            (
                _clamp(base[0] + wave, 0, 255),
                _clamp(base[1] + wave, 0, 255),
                _clamp(base[2] + wave + 2, 0, 255),
            ),
        )
    image = gradient.resize(size).convert("RGBA")
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    variant_offset = variant * 0.18
    first_x = width * (0.14 + 0.20 * settle + 0.03 * math.sin(math.tau * (progress + variant_offset)))
    first_y = height * (0.16 + 0.05 * math.sin(math.tau * (progress + 0.2 + variant_offset)))
    first_radius = 170 + 35 * settle + variant * 12
    draw.ellipse(
        (first_x - first_radius, first_y - first_radius, first_x + first_radius, first_y + first_radius),
        fill=SOFT_BLUE + (42,),
    )

    second_x = width * (0.82 - 0.16 * settle + 0.02 * math.sin(math.tau * (progress + 0.45 - variant_offset)))
    second_y = height * (0.74 + 0.04 * math.cos(math.tau * (progress + 0.1 + variant_offset)))
    second_radius = 210 + 45 * settle - variant * 15
    draw.ellipse(
        (second_x - second_radius, second_y - second_radius, second_x + second_radius, second_y + second_radius),
        fill=PALE_BLUE + (54,),
    )

    band_direction = -1 if variant % 2 else 1
    band_position = progress if band_direction > 0 else 1 - progress
    band_x = width * (-0.25 + 1.45 * band_position)
    draw.polygon(
        [(band_x, 0), (band_x + 190, 0), (band_x + 60, height), (band_x - 130, height)],
        fill=(255, 255, 255, 34),
    )
    for index in range(16):
        seed = index * 0.117
        particle_x = width * ((seed + progress * (0.16 + index % 4 * 0.035)) % 1.15 - 0.075)
        particle_y = height * ((0.92 - seed % 0.8 - progress * (0.08 + index % 3 * 0.025)) % 1.05 - 0.025)
        particle_radius = 4 + (index % 5) * 3
        particle_alpha = 34 + (index % 4) * 12
        draw.ellipse(
            (
                particle_x - particle_radius,
                particle_y - particle_radius,
                particle_x + particle_radius,
                particle_y + particle_radius,
            ),
            fill=(255, 255, 255, particle_alpha),
        )

    ring_center_x = width * (0.76 + 0.025 * math.sin(math.tau * progress + variant))
    ring_center_y = height * (0.28 + 0.025 * math.cos(math.tau * progress + variant))
    ring_radius = 128 + 18 * math.sin(math.tau * progress * 1.5 + variant)
    draw.arc(
        (
            ring_center_x - ring_radius,
            ring_center_y - ring_radius,
            ring_center_x + ring_radius,
            ring_center_y + ring_radius,
        ),
        start=math.degrees(math.tau * progress),
        end=math.degrees(math.tau * progress + 1.35),
        fill=(255, 255, 255, 62),
        width=5,
    )
    return Image.alpha_composite(image, overlay)

def footer_text(scene: Scene, source: str) -> str:
    return f"Sumber: {scene.source or source}"

def hook_for_frame(scene: Scene, elapsed_seconds: float, total_duration: float) -> str:
    if not scene.hook:
        return ""
    return scene.hook if elapsed_seconds < 3.0 else ""


def _card(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    reveal: float,
    slide: int = 28,
) -> int:
    left, top, right, bottom = box
    offset = round((1 - reveal) * slide)
    animated_box = (left, top + offset, right, bottom + offset)
    alpha = round(235 * reveal)
    draw.rounded_rectangle(
        (animated_box[0] + 5, animated_box[1] + 8, animated_box[2] + 5, animated_box[3] + 8),
        radius=30,
        fill=(15, 23, 42, 18),
    )
    draw.rounded_rectangle(animated_box, radius=30, fill=CARD_COLOR + (alpha,), outline=(219, 234, 254, alpha))
    return offset


def _extract_metrics(caption: str) -> list[str]:
    values = re.findall(
        r"(?:Rp\s?[\d.]+(?:/\s?\w+)?|\d+(?:[.,]\d+)?\s?persen|\d{1,2}[.:]\d{2}\s?(?:WITA|WIB|WIT))",
        caption,
        flags=re.IGNORECASE,
    )
    return values[:3]


def split_process_steps(caption: str) -> list[str]:
    steps = [part.strip() for part in re.split(r"(?<=[.!?])\s+", caption) if part.strip()]
    return steps[:3]


def _draw_headline_block(
    layer: Image.Image,
    scene: Scene,
    article_title: str,
    reveal: float,
    width: int,
) -> None:
    draw = ImageDraw.Draw(layer)
    panel_top = 108 + round((1 - reveal) * 24)
    panel_offset = _card(draw, (46, panel_top, width - 46, 418), reveal)
    top = panel_top + panel_offset
    draw.text((82, top + 34), scene.heading.upper(), font=_load_font(28), fill=BLUE_COLOR + (255,))
    title_lines = layout_text(article_title, 24)[:4]
    line_stagger = stagger_step(scene.duration)
    y = top + 88
    for index, line in enumerate(title_lines):
        line_reveal = ease_out_strong(_clamp(reveal - index * line_stagger))
        offset = round((1 - line_reveal) * 16)
        draw.text(
            (82, y + offset),
            line,
            font=_load_font(38),
            fill=INK_COLOR + (round(255 * line_reveal),),
        )
        y += 50

    underline_reveal = ease_out_cubic(_clamp(reveal * 1.4))
    underline_width = round((width - 164) * underline_reveal)
    draw.rounded_rectangle(
        (82, y + 4, 82 + underline_width, y + 12),
        radius=4,
        fill=BLUE_COLOR + (round(255 * underline_reveal),),
    )


def _draw_caption_card(
    layer: Image.Image,
    scene: Scene,
    reveal: float,
    width: int,
    height: int,
) -> None:
    draw = ImageDraw.Draw(layer)
    caption_lines = layout_text(scene.caption, 32)[:5]
    line_stagger = stagger_step(scene.duration)
    card_height = 110 + len(caption_lines) * 46
    card_top = round(height * 0.60)
    card_offset = _card(draw, (46, card_top, width - 46, card_top + card_height), reveal, slide=34)
    top = card_top + card_offset
    draw.text((82, top + 30), "POIN UTAMA", font=_load_font(21), fill=BLUE_COLOR + (255,))
    y = top + 68
    for index, line in enumerate(caption_lines):
        line_reveal = ease_out_strong(_clamp(reveal - index * line_stagger))
        draw.text(
            (82, y + round((1 - line_reveal) * 12)),
            line,
            font=_load_font(31),
            fill=INK_COLOR + (round(235 * line_reveal),),
        )
        y += 46


def _draw_metric_layout(
    layer: Image.Image,
    scene: Scene,
    article_title: str,
    reveal: float,
    settle: float,
    width: int,
    height: int,
) -> None:
    _draw_headline_block(layer, scene, article_title, reveal, width)
    draw = ImageDraw.Draw(layer)
    metrics = _extract_metrics(scene.caption) or ["Data dipantau"]
    metric_stagger = stagger_step(scene.duration)
    card_top = round(height * 0.52)
    card_offset = _card(draw, (46, card_top, width - 46, card_top + 390), reveal, slide=32)
    top = card_top + card_offset
    draw.text((82, top + 32), "DATA KUNCI", font=_load_font(24), fill=BLUE_COLOR + (255,))
    shimmer_x = 46 + (width - 92) * ((settle * 1.35) % 1)
    draw.line((shimmer_x, top + 18, shimmer_x + 26, top + 372), fill=(255, 255, 255, 105), width=8)
    for index, metric in enumerate(metrics):
        metric_reveal = ease_out_strong(_clamp(reveal - index * metric_stagger))
        y = top + 86 + index * 84
        bar_width = round((width - 164) * (0.94 - index * 0.16) * metric_reveal)
        draw.rounded_rectangle(
            (82, y + 34, width - 82, y + 48),
            radius=7,
            fill=PALE_BLUE + (255,),
        )
        draw.rounded_rectangle(
            (82, y + 34, 82 + bar_width, y + 48),
            radius=7,
            fill=BLUE_COLOR + (255,),
        )
        draw.text((82, y - 6), metric, font=_load_font(34), fill=INK_COLOR + (round(255 * metric_reveal),))

def _draw_detail_layout(
    layer: Image.Image,
    scene: Scene,
    article_title: str,
    reveal: float,
    settle: float,
    width: int,
    height: int,
) -> None:
    _draw_headline_block(layer, scene, article_title, reveal, width)
    draw = ImageDraw.Draw(layer)
    discussion = layout_text(scene.caption, 38)[:7]
    card_top = round(height * 0.46)
    card_offset = _card(draw, (46, card_top, width - 46, card_top + 540), reveal, slide=36)
    top = card_top + card_offset
    draw.text((82, top + 34), "PEMBAHASAN LENGKAP", font=_load_font(24), fill=BLUE_COLOR + (255,))

    labels = ["Konteks", "Fakta", "Tindak lanjut"]
    accent_positions = [(82, top + 100), (82, top + 240), (82, top + 380)]
    label_stagger = stagger_step(scene.duration)
    connector_reveal = ease_out_cubic(_clamp(settle * 1.8))
    connector_top = top + 128
    connector_bottom = connector_top + round(252 * connector_reveal)
    draw.line((87, connector_top, 87, connector_bottom), fill=PALE_BLUE + (round(235 * connector_reveal),), width=3)
    pulse_y = connector_top + (connector_bottom - connector_top) * ((settle * 1.8) % 1)
    pulse_radius = 5 + 2 * math.sin(math.tau * settle * 2)
    draw.ellipse(
        (87 - pulse_radius, pulse_y - pulse_radius, 87 + pulse_radius, pulse_y + pulse_radius),
        fill=BLUE_COLOR + (round(190 * connector_reveal),),
    )
    for index, label in enumerate(labels):
        label_reveal = ease_out_strong(_clamp(reveal - index * label_stagger))
        x, y = accent_positions[index]
        draw.rounded_rectangle(
            (x, y, x + 10, y + 58),
            radius=5,
            fill=BLUE_COLOR + (round(255 * label_reveal),),
        )
        draw.text(
            (x + 24, y - 4),
            label.upper(),
            font=_load_font(22),
            fill=BLUE_COLOR + (round(255 * label_reveal),),
        )
        start_index = index * 2
        for line_index, line in enumerate(discussion[start_index:start_index + 2]):
            line_reveal = ease_out_cubic(_clamp(label_reveal * 1.3 - line_index * 0.14))
            draw.text(
                (x + 24, y + 28 + line_index * 35),
                line,
                font=_load_font(25),
                fill=INK_COLOR + (round(235 * line_reveal),),
            )


def _draw_process_layout(
    layer: Image.Image,
    scene: Scene,
    article_title: str,
    reveal: float,
    settle: float,
    width: int,
    height: int,
) -> None:
    _draw_headline_block(layer, scene, article_title, reveal, width)
    draw = ImageDraw.Draw(layer)
    steps = split_process_steps(scene.caption)
    if len(steps) < 2:
        steps = [scene.caption]
    step_stagger = stagger_step(scene.duration)
    card_top = round(height * 0.52)
    card_offset = _card(draw, (46, card_top, width - 46, card_top + 110 + len(steps) * 92), reveal)
    top = card_top + card_offset
    draw.text((82, top + 32), "LANGKAH", font=_load_font(24), fill=BLUE_COLOR + (255,))
    path_reveal = ease_out_cubic(_clamp(settle * 1.7))
    path_bottom = top + 114 + round((len(steps) - 1) * 92 * path_reveal)
    draw.line((108, top + 114, 108, path_bottom), fill=PALE_BLUE + (round(235 * path_reveal),), width=4)
    pulse_y = top + 114 + (path_bottom - top - 114) * ((settle * 1.65) % 1)
    draw.ellipse((100, pulse_y - 8, 116, pulse_y + 8), fill=BLUE_COLOR + (175,))
    for index, step in enumerate(steps):
        step_reveal = ease_out_strong(_clamp(reveal - index * step_stagger))
        y = top + 88 + index * 92
        draw.ellipse(
            (82, y, 134, y + 52),
            fill=BLUE_COLOR + (round(235 * step_reveal),),
        )
        draw.text((99, y + 9), str(index + 1), font=_load_font(26), fill=(255, 255, 255, 255))
        step_lines = layout_text(step, 28)[:2]
        for line_index, line in enumerate(step_lines):
            draw.text(
                (154, y + line_index * 34),
                line,
                font=_load_font(28),
                fill=INK_COLOR + (round(235 * step_reveal),),
            )


def _draw_conclusion_layout(
    layer: Image.Image,
    scene: Scene,
    article_title: str,
    reveal: float,
    settle: float,
    width: int,
    height: int,
) -> None:
    _draw_headline_block(layer, scene, article_title, reveal, width)
    draw = ImageDraw.Draw(layer)
    card_top = round(height * 0.50)
    card_offset = _card(draw, (46, card_top, width - 46, card_top + 430), reveal)
    top = card_top + card_offset
    draw.text((82, top + 36), "KESIMPULAN", font=_load_font(24), fill=BLUE_COLOR + (255,))
    ring_reveal = ease_out_cubic(_clamp(settle * 1.5))
    draw.arc(
        (82, top + 88, 174, top + 180),
        start=-90,
        end=360 * ring_reveal,
        fill=BLUE_COLOR,
        width=12,
    )
    if ring_reveal > 0.85:
        draw.line((110, top + 135, 126, top + 153), fill=BLUE_COLOR, width=10)
        draw.line((126, top + 153, 152, top + 112), fill=BLUE_COLOR, width=10)
    for index in range(4):
        orbit_angle = math.tau * (settle * (0.55 + index * 0.06) + index / 4)
        orbit_x = 128 + 82 * math.cos(orbit_angle)
        orbit_y = top + 134 + 82 * math.sin(orbit_angle)
        orbit_radius = 5 + index % 3
        draw.ellipse(
            (orbit_x - orbit_radius, orbit_y - orbit_radius, orbit_x + orbit_radius, orbit_y + orbit_radius),
            fill=SOFT_BLUE + (round(150 * ring_reveal),),
        )
    caption_lines = layout_text(scene.caption, 30)[:4]
    line_stagger = stagger_step(scene.duration)
    y = top + 210
    for index, line in enumerate(caption_lines):
        line_reveal = ease_out_strong(_clamp(reveal - index * line_stagger))
        draw.text(
            (82, y + round((1 - line_reveal) * 14)),
            line,
            font=_load_font(31),
            fill=INK_COLOR + (round(240 * line_reveal),),
        )
        y += 48


def render_scene_image(
    scene: Scene,
    article_title: str,
    source: str,
    progress: float = 1.0,
    size: tuple[int, int] = (720, 1280),
    total_duration: float = 30.0,
) -> Image.Image:
    width, height = size
    article_title = scene.title or article_title
    source = scene.source or source
    local = _local_progress(scene, progress, total_duration)
    entrance_progress = min(
        0.34,
        MOTION_TOKENS["enter_duration_seconds"] / max(scene.duration, 0.001),
    )
    reveal = ease_out_strong(_clamp(local / entrance_progress))
    settle = ease_in_out_strong(local)
    image = _background(size, progress, settle, scene.index - 1)

    content_layer = Image.new("RGBA", size, (0, 0, 0, 0))
    _draw_layout_motif(content_layer, scene.layout, local, width, height)
    if scene.layout == "metrics":
        _draw_metric_layout(content_layer, scene, article_title, reveal, settle, width, height)
    elif scene.layout == "detail":
        _draw_detail_layout(content_layer, scene, article_title, reveal, settle, width, height)
    elif scene.layout == "process":
        _draw_process_layout(content_layer, scene, article_title, reveal, settle, width, height)
    elif scene.layout == "conclusion":
        _draw_conclusion_layout(content_layer, scene, article_title, reveal, settle, width, height)
    else:
        _draw_headline_block(content_layer, scene, article_title, reveal, width)
        _draw_caption_card(content_layer, scene, reveal, width, height)

    layer = _animate_layer(content_layer, _layout_motion(scene.layout, local))

    hook_text = hook_for_frame(scene, _local_progress(scene, progress, total_duration) * scene.duration, total_duration)
    if hook_text:
        hook_lines = layout_text(hook_text, 26)[:3]
        hook_height = 150 + len(hook_lines) * 56
        hook_top = round(height * 0.235)
        hook_reveal = ease_out_strong(_clamp(local / 0.18))
        hook_offset = round((1 - hook_reveal) * 24)
        hook_draw = ImageDraw.Draw(layer)
        hook_draw.rounded_rectangle(
            (46, hook_top + hook_offset, width - 46, hook_top + hook_height + hook_offset),
            radius=34,
            fill=(255, 255, 255, round(245 * hook_reveal)),
            outline=BLUE_COLOR + (round(255 * hook_reveal),),
            width=3,
        )
        hook_draw.text((82, hook_top + hook_offset + 34), "HOOK", font=_load_font(24), fill=BLUE_COLOR + (round(255 * hook_reveal),))
        hook_y = hook_top + hook_offset + 82
        for line_index, line in enumerate(hook_lines):
            line_reveal = ease_out_strong(_clamp(hook_reveal - line_index * stagger_step(scene.duration)))
            hook_draw.text(
                (82, hook_y + round((1 - line_reveal) * 14)),
                line,
                font=_load_font(38),
                fill=INK_COLOR + (round(255 * line_reveal),),
            )
            hook_y += 56

    draw = ImageDraw.Draw(layer)
    draw.text((52, height - 76), footer_text(scene, source), font=_load_font(22), fill=MUTED_COLOR + (235,))
    draw.rounded_rectangle((52, height - 48, width - 52, height - 34), radius=7, fill=PALE_BLUE + (255,))
    bar_end = 52 + round((width - 104) * ease_out_cubic(progress))
    draw.rounded_rectangle((52, height - 48, bar_end, height - 34), radius=7, fill=BLUE_COLOR + (255,))

    edge_alpha = 1 - _clamp(min(local / 0.08, (1 - local) / 0.08))
    if edge_alpha > 0:
        edge = Image.new("RGBA", size, (255, 255, 255, round(150 * edge_alpha)))
        layer = Image.alpha_composite(layer, edge)

    return Image.alpha_composite(image, layer).convert("RGB")


def render_scene_frames(
    scene: Scene,
    plan: VideoPlan,
    scene_dir: Path,
    fps: int,
    rendered: int,
    total_frames: int,
) -> int:
    scene_dir.mkdir(parents=True, exist_ok=True)
    frame_count = round(scene.duration * fps)
    for frame_index in range(frame_count):
        progress = (rendered + frame_index + 1) / total_frames
        image = render_scene_image(
            scene,
            plan.title,
            plan.source,
            progress=progress,
            total_duration=plan.duration_seconds,
        )
        image.save(scene_dir / f"frame_{frame_index:04d}.png")
    return frame_count


def render_frames(
    plan: VideoPlan,
    build_dir: Path,
    fps: int = 24,
) -> None:
    total_frames = sum(round(scene.duration * fps) for scene in plan.scenes)
    rendered = 0
    for scene in plan.scenes:
        rendered += render_scene_frames(
            scene,
            plan,
            build_dir / f"scene_{scene.index:02d}",
            fps,
            rendered,
            total_frames,
        )


def _ffmpeg_executable() -> str:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        found = shutil.which("ffmpeg")
        if not found:
            raise RuntimeError("ffmpeg tidak ditemukan; install imageio-ffmpeg")
        return found


def _audio_duration(audio_path: Path, ffmpeg: str) -> float:
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


def render_article_video(
    plan: VideoPlan,
    output_path: str | Path,
    tts_engine: EdgeTTSEngine | None = None,
    fps: int = 24,
) -> Path:
    engine = tts_engine or EdgeTTSEngine()
    output = Path(output_path).resolve()
    build_dir = output.parent / f"{output.stem}_build"
    build_dir.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = _ffmpeg_executable()

    scene_paths = []
    audio_paths = []
    for scene in plan.scenes:
        audio_path = build_dir / f"scene_{scene.index:02d}.mp3"
        engine.synthesize(scene.narration, audio_path, plan.voice)
        audio_paths.append(audio_path)

    audio_durations = [_audio_duration(audio_path, ffmpeg) for audio_path in audio_paths]
    synced_plan = adjust_plan_to_audio(plan, audio_durations)
    total_frames = sum(round(scene.duration * fps) for scene in synced_plan.scenes)
    rendered = 0
    for scene in plan.scenes:
        synced_scene = synced_plan.scenes[scene.index - 1]
        audio_path = audio_paths[scene.index - 1]
        scene_path = build_dir / f"scene_{scene.index:02d}.mp4"
        scene_dir = build_dir / f"scene_{scene.index:02d}"
        rendered += render_scene_frames(
            synced_scene,
            synced_plan,
            scene_dir,
            fps,
            rendered,
            total_frames,
        )
        command = build_ffmpeg_scene_args(
            frame_pattern=str(scene_dir / "frame_%04d.png"),
            audio_path=str(audio_path),
            output_path=str(scene_path),
            duration=synced_scene.duration,
            fps=fps,
        )
        command[0] = ffmpeg
        subprocess.run(command, check=True, cwd=build_dir)
        scene_paths.append(scene_path.name)

    concat_path = build_dir / "concat.txt"
    concat_path.write_text("\n".join(f"file '{path}'" for path in scene_paths), encoding="utf-8")
    command = build_concat_args(
        concat_list_path=concat_path.name,
        output_path=str(output),
    )
    command[0] = ffmpeg
    subprocess.run(command, check=True, cwd=build_dir)
    return output
