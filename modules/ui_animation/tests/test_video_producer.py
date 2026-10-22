import unittest

from modules.ui_animation.producer import (
    Scene,
    build_ffmpeg_scene_args,
    build_concat_args,
    build_video_plan,
    adjust_plan_to_audio,
    build_news_roundup_plan,
    html_to_text,
    layout_text,
)
from modules.ui_animation.renderer import render_scene_image
from modules.ui_animation.renderer import ease_out_cubic
from modules.ui_animation.renderer import _extract_metrics
from modules.ui_animation.renderer import split_process_steps
from modules.ui_animation.renderer import _layout_motion
from modules.ui_animation.renderer import footer_text
from modules.ui_animation.renderer import MOTION_TOKENS
from modules.ui_animation.renderer import ease_in_out_strong
from modules.ui_animation.renderer import ease_out_strong
from modules.ui_animation.renderer import stagger_step
from modules.ui_animation.renderer import hook_for_frame
from modules.ui_animation.renderer import _layout_motif_motion
from modules.ui_animation.renderer import EMOTION_MOTION_STYLE
from modules.ui_animation.renderer import REMOTION_UI_STYLE
from modules.ui_animation.renderer import _emotion_camera
from modules.ui_animation.renderer import _emotion_parallax
from modules.ui_animation.renderer import _emotion_stage
from modules.ui_animation.renderer import EdgeTTSEngine as RendererEdgeTTSEngine
from modules.ui_animation.article_provider import load_article, load_latest_kaltim_articles
from modules.ui_animation import (
    EdgeTTSEngine,
    EMOTION_MOTION_STYLE,
    render_article_video,
    render_scene_image,
)
from modules.ui_animation.cli import build_roundup_plan


class VideoProducerTests(unittest.TestCase):
    def test_html_to_text_removes_markup_and_entities(self):
        raw = "<p>Pemerintah&nbsp;Kota <b>Samarinda</b> memperketat pengawasan.</p>"

        self.assertEqual(
            html_to_text(raw),
            "Pemerintah Kota Samarinda memperketat pengawasan.",
        )

    def test_build_video_plan_creates_thirty_second_synced_scenes(self):
        article = {
            "title": "Pemkot Samarinda perketat pengawasan pasokan cabai dan BBM subsidi",
            "summary": "<p>Penguatan koordinasi lintas sektor dilakukan untuk menjaga stabilitas ekonomi.</p>",
            "source": "Antara Kaltim",
            "url": "https://example.test/article",
        }

        plan = build_video_plan(
            article,
            narration_points=[
                "Harga cabai naik karena kendala distribusi.",
                "Beberapa komoditas melewati batas harga tertinggi.",
                "Stok pangan dipantau dan Gerakan Pangan Murah disiapkan.",
            ],
            conclusion="Tujuannya menjaga inflasi dan memastikan BBM subsidi tepat sasaran.",
            duration_seconds=30,
        )

        self.assertEqual(plan.duration_seconds, 30)
        self.assertEqual(len(plan.scenes), 4)
        self.assertEqual([scene.duration for scene in plan.scenes], [7.5, 7.5, 7.5, 7.5])
        self.assertEqual(plan.scenes[0].start, 0.0)
        self.assertEqual(plan.scenes[-1].end, 30.0)
        self.assertIn("Pemkot Samarinda", plan.scenes[0].narration)
        self.assertIn("Harga cabai naik", plan.scenes[1].narration)
        self.assertIn("Beberapa komoditas", plan.scenes[2].narration)
        self.assertNotIn("Stok pangan", plan.scenes[2].narration)
        self.assertIn("Tujuannya menjaga inflasi", plan.scenes[3].narration)
        self.assertIn("Antara Kaltim", plan.scenes[3].narration)
        self.assertEqual(plan.voice, "id-ID-ArdiNeural")
        self.assertTrue(all(len(scene.narration) <= 130 for scene in plan.scenes))
        self.assertEqual(
            [scene.layout for scene in plan.scenes],
            ["headline", "metrics", "process", "conclusion"],
        )

    def test_layout_text_keeps_vertical_captions_readable(self):
        lines = layout_text(
            "Harga cabai naik karena kendala distribusi di Samarinda",
            max_characters=24,
        )

        self.assertTrue(lines)
        self.assertTrue(all(len(line) <= 24 for line in lines))
        self.assertEqual(" ".join(lines), "Harga cabai naik karena kendala distribusi di Samarinda")

    def test_ffmpeg_scene_args_pad_audio_and_force_duration(self):
        args = build_ffmpeg_scene_args(
            frame_pattern="build/scene_01/frame_%04d.png",
            audio_path="build/scene_01.mp3",
            output_path="build/scene_01.mp4",
            duration=7.5,
        )

        self.assertIn("-y", args)
        self.assertIn("-framerate", args)
        self.assertIn("build/scene_01/frame_%04d.png", args)
        self.assertIn("[1:a]apad=whole_dur=7.5[a]", args)
        self.assertIn("-t", args)
        self.assertIn("7.5", args)
        self.assertIn("build/scene_01.mp4", args)

    def test_render_scene_image_creates_vertical_frame(self):
        scene = build_video_plan(
            {"title": "Judul berita", "source": "Antara Kaltim", "url": "https://example.test"},
            conclusion="Kesimpulan berita.",
        ).scenes[0]

        image = render_scene_image(scene, "Judul berita", "Antara Kaltim")

        self.assertEqual(image.size, (720, 1280))
        self.assertEqual(image.mode, "RGB")

    def test_render_detail_scene_shows_discussion_points(self):
        articles = [
            {
                "title": "Berita Kaltim 1",
                "summary": "Isi berita.",
                "content": "Latar belakang menjelaskan kondisi awal. Fakta utama menjelaskan dampak langsung. Tindak lanjut mencakup pemantauan dan evaluasi.",
                "source": "Antara Kaltim",
                "url": "https://example.test/1",
            }
        ] * 3
        plan = build_news_roundup_plan(articles, duration_seconds=60)
        scene = plan.scenes[1]

        image = render_scene_image(
            scene,
            plan.title,
            plan.source,
            progress=0.5,
            total_duration=plan.duration_seconds,
        )

        self.assertEqual(image.size, (720, 1280))
        self.assertEqual(scene.layout, "detail")

        same_headline = Scene(
            index=scene.index,
            start=scene.start,
            end=scene.end,
            duration=scene.duration,
            heading=scene.heading,
            narration=scene.narration,
            caption=scene.caption,
            layout="headline",
            title=scene.title,
            source=scene.source,
        )
        headline_image = render_scene_image(
            same_headline,
            plan.title,
            plan.source,
            progress=0.5,
            total_duration=plan.duration_seconds,
        )
        self.assertNotEqual(image.tobytes(), headline_image.tobytes())

    def test_render_scene_image_uses_soft_white_blue_palette(self):
        scene = build_video_plan(
            {"title": "Judul berita", "source": "Antara Kaltim", "url": "https://example.test"},
            conclusion="Kesimpulan berita.",
        ).scenes[0]

        image = render_scene_image(scene, "Judul berita", "Antara Kaltim", progress=0.5)

        top = image.getpixel((6, 6))
        bottom = image.getpixel((6, 1274))
        for pixel in (top, bottom):
            red, green, blue = pixel
            self.assertGreaterEqual(red, 205)
            self.assertGreaterEqual(green, 220)
            self.assertGreaterEqual(blue, 235)
            self.assertGreaterEqual(blue, red - 8)

    def test_easing_and_progress_create_smooth_motion(self):
        self.assertEqual(ease_out_cubic(0.0), 0.0)
        self.assertEqual(ease_out_cubic(1.0), 1.0)
        self.assertGreater(ease_out_cubic(0.25), 0.25)
        self.assertLess(ease_out_cubic(0.75), 1.0)

        scene = build_video_plan(
            {"title": "Judul berita", "source": "Antara Kaltim", "url": "https://example.test"},
            conclusion="Kesimpulan berita.",
        ).scenes[0]

        first = render_scene_image(scene, "Judul berita", "Antara Kaltim", progress=0.25)
        second = render_scene_image(scene, "Judul berita", "Antara Kaltim", progress=0.5)

        self.assertNotEqual(first.tobytes(), second.tobytes())

    def test_scene_frames_do_not_repeat_and_preserve_remotion_contrast(self):
        scene = build_video_plan(
            {"title": "Judul berita", "source": "Antara Kaltim", "url": "https://example.test"},
            conclusion="Kesimpulan berita.",
        ).scenes[0]

        frames = [
            render_scene_image(scene, "Judul berita", "Antara Kaltim", progress=value)
            for value in (0.01, 0.03, 0.06, 0.09)
        ]

        signatures = [frame.tobytes() for frame in frames]
        self.assertEqual(len(signatures), len(set(signatures)))

        final_frame = render_scene_image(
            scene,
            "Judul berita",
            "Antara Kaltim",
            progress=0.9,
        )
        darkest = min(final_frame.getdata(), key=lambda pixel: sum(pixel[:3]))
        self.assertLess(sum(darkest[:3]), 120)

    def test_first_progress_bar_frame_does_not_draw_invalid_rectangle(self):
        plan = build_video_plan(
            {"title": "Judul berita", "source": "Antara Kaltim", "url": "https://example.test"},
            conclusion="Kesimpulan berita.",
            duration_seconds=180,
        )
        first_progress = 1 / (plan.duration_seconds * 24)

        image = render_scene_image(
            plan.scenes[0],
            plan.title,
            plan.source,
            progress=first_progress,
            total_duration=plan.duration_seconds,
        )

        self.assertEqual(image.size, (720, 1280))

    def test_metric_layout_extracts_informative_values(self):
        metrics = _extract_metrics(
            "Mati lampu pukul 10.00 WITA. Cabai Rp91.300/kg dan BBM naik 9,6 persen."
        )

        self.assertIn("10.00 WITA", metrics)
        self.assertIn("Rp91.300/kg", metrics)
        self.assertIn("9,6 persen", metrics)

    def test_process_steps_keep_decimal_numbers_together(self):
        steps = split_process_steps("Konsumsi BBM subsidi naik 9,6 persen.")

        self.assertEqual(steps, ["Konsumsi BBM subsidi naik 9,6 persen."])

    def test_package_exports_animation_api(self):
        self.assertTrue(callable(render_article_video))
        self.assertTrue(callable(render_scene_image))
        self.assertEqual(EMOTION_MOTION_STYLE["entrance_seconds"], 0.18)
        self.assertIs(EdgeTTSEngine, RendererEdgeTTSEngine)

    def test_build_concat_args_copies_scene_videos(self):
        args = build_concat_args(
            concat_list_path="build/concat.txt",
            output_path="public/video.mp4",
        )

        self.assertIn("-f", args)
        self.assertIn("concat", args)
        self.assertIn("-safe", args)
        self.assertIn("0", args)
        self.assertIn("-c", args)
        self.assertIn("copy", args)
        self.assertIn("public/video.mp4", args)

    def test_load_article_from_mysql_by_url(self):
        class FakeCursor:
            def __init__(self):
                self.query = ""
                self.params = ()

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                return False

            def execute(self, query, params=()):
                self.query = query
                self.params = params

            def fetchone(self):
                return {
                    "url": "https://example.test/article",
                    "title": "Judul",
                    "source": "Antara Kaltim",
                    "region": "kaltim",
                    "summary": "<p>Isi</p>",
                    "published_at": "2026-10-21 06:23:04",
                }

        class FakeConnection:
            def cursor(self):
                return FakeCursor()

        article = load_article(FakeConnection(), "https://example.test/article")

        self.assertEqual(article["region"], "kaltim")
        self.assertEqual(article["title"], "Judul")

    def test_load_latest_kaltim_articles_returns_three_articles(self):
        class FakeCursor:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                return False

            def execute(self, query, params=()):
                self.query = query
                self.params = params

            def fetchall(self):
                return [
                    {"url": f"https://example.test/{index}", "title": f"Berita {index}", "source": "Antara Kaltim", "region": "kaltim", "summary": "<p>Isi</p>", "published_at": "2026-10-21 06:00:00"}
                    for index in range(1, 4)
                ]

        class FakeConnection:
            def cursor(self):
                return FakeCursor()

        articles = load_latest_kaltim_articles(FakeConnection(), limit=3)

        self.assertEqual(len(articles), 3)
        self.assertEqual(articles[0]["title"], "Berita 1")

    def test_build_news_roundup_plan_creates_three_news_and_closing(self):
        articles = [
            {
                "title": f"Berita Kaltim {index}",
                "summary": f"<p>Isi berita {index} yang informatif.</p>",
                "content": f"Latar belakang berita {index} menjelaskan kondisi awal, pihak yang terlibat, dan alasan peristiwa ini penting. Fakta utama menjelaskan dampak langsung bagi masyarakat, termasuk perubahan aktivitas dan risiko yang perlu diantisipasi. Tindak lanjut yang dilakukan mencakup pemantauan lapangan, koordinasi lintas instansi, penyediaan layanan alternatif, serta evaluasi berkala agar keputusan tetap sesuai kondisi terbaru.",
                "source": "Antara Kaltim",
                "url": f"https://example.test/{index}",
            }
            for index in range(1, 4)
        ]

        plan = build_news_roundup_plan(articles, duration_seconds=60)

        self.assertEqual(len(plan.scenes), 7)
        self.assertEqual(
            [scene.layout for scene in plan.scenes],
            ["headline", "detail", "metrics", "detail", "process", "detail", "conclusion"],
        )
        self.assertEqual(plan.scenes[0].title, "Berita Kaltim 1")
        self.assertEqual(plan.scenes[1].title, "Berita Kaltim 1")
        self.assertEqual(plan.scenes[2].title, "Berita Kaltim 2")
        self.assertEqual(plan.scenes[3].title, "Berita Kaltim 2")
        self.assertEqual(plan.scenes[4].title, "Berita Kaltim 3")
        self.assertEqual(plan.scenes[5].title, "Berita Kaltim 3")
        self.assertEqual(plan.scenes[6].title, "Ringkasan Kaltim")
        self.assertIn("Latar belakang berita 1", plan.scenes[1].narration)
        self.assertIn("Fakta utama", plan.scenes[1].narration)
        self.assertIn("Latar belakang berita 2", plan.scenes[3].narration)
        self.assertIn("Latar belakang berita 3", plan.scenes[5].narration)
        self.assertIn("tiga berita Kaltim", plan.scenes[6].narration)
        self.assertIn("dampak", plan.scenes[6].narration)
        self.assertIn("tindak lanjut", plan.scenes[6].narration)
        self.assertEqual([scene.source for scene in plan.scenes[:6]], ["Antara Kaltim"] * 6)
        self.assertTrue(all(len(scene.narration) >= 300 for scene in plan.scenes[1::2]))
        self.assertGreaterEqual(len(plan.scenes[6].narration), 260)

    def test_roundup_narration_discusses_content_without_reading_titles(self):
        articles = [
            {
                "title": f"Judul Khusus Nomor {index}",
                "summary": f"Isi berita {index} yang informatif.",
                "content": f"Latar belakang berita {index} menjelaskan kondisi awal, pihak yang terlibat, dan alasan peristiwa ini penting. Fakta utama menjelaskan dampak langsung bagi masyarakat, termasuk perubahan aktivitas dan risiko yang perlu diantisipasi. Tindak lanjut yang dilakukan mencakup pemantauan lapangan, koordinasi lintas instansi, penyediaan layanan alternatif, serta evaluasi berkala agar keputusan tetap sesuai kondisi terbaru.",
                "source": "Antara Kaltim",
                "url": f"https://example.test/{index}",
            }
            for index in range(1, 4)
        ]

        plan = build_news_roundup_plan(articles, duration_seconds=60)

        for index, article in enumerate(articles):
            intro = plan.scenes[index * 2].narration.lower()
            detail = plan.scenes[index * 2 + 1].narration.lower()
            self.assertNotIn(article["title"].lower(), intro)
            self.assertNotIn(article["title"].lower(), detail)
            self.assertGreaterEqual(len(plan.scenes[index * 2].narration), 180)
            self.assertGreaterEqual(len(detail), 300)

    def test_footer_does_not_show_scene_counter(self):
        scene = build_video_plan(
            {"title": "Judul berita", "source": "Antara Kaltim", "url": "https://example.test"}
        ).scenes[0]

        text = footer_text(scene, "Antara Kaltim")

        self.assertEqual(text, "Sumber: Antara Kaltim")
        self.assertNotIn("Scene", text)

    def test_layout_motion_is_continuous_and_varied(self):
        layouts = ["headline", "detail", "metrics", "process", "conclusion"]
        motions = [_layout_motion(layout, 0.55) for layout in layouts]

        self.assertEqual(len(motions), len(set(motions)))
        for layout in layouts:
            values = [_layout_motion(layout, progress) for progress in (0.25, 0.55, 0.85)]
            self.assertEqual(len(values), len(set(values)))
            for offset_x, offset_y, scale, rotation in values:
                self.assertGreaterEqual(abs(offset_x) + abs(offset_y), 18)
                self.assertGreaterEqual(abs(rotation), 1.2)
                self.assertGreaterEqual(scale, 1.02)

    def test_layout_motifs_are_continuous_and_layout_specific(self):
        layouts = ["headline", "detail", "metrics", "process", "conclusion"]
        first = [_layout_motif_motion(layout, 0.25) for layout in layouts]
        second = [_layout_motif_motion(layout, 0.75) for layout in layouts]

        self.assertEqual(len(first), len(set(first)))
        self.assertEqual(len(second), len(set(second)))
        for layout in layouts:
            self.assertNotEqual(_layout_motif_motion(layout, 0.25), _layout_motif_motion(layout, 0.75))

    def test_emotion_motion_style_is_primary_and_spatial(self):
        self.assertEqual(EMOTION_MOTION_STYLE["camera_amplitude"], (26.0, 18.0))
        self.assertEqual(EMOTION_MOTION_STYLE["camera_rotation_degrees"], 1.8)
        self.assertEqual(EMOTION_MOTION_STYLE["parallax_depths"], (0.18, 0.46, 1.0))
        self.assertEqual(EMOTION_MOTION_STYLE["entrance_seconds"], 0.18)
        self.assertEqual(EMOTION_MOTION_STYLE["beat_seconds"], 0.04)

    def test_emotion_camera_is_continuous_and_varies_by_scene(self):
        for progress in (0.25, 0.55, 0.85):
            values = [_emotion_camera(progress, variant) for variant in range(4)]
            self.assertEqual(len(values), len(set(values)))
            for camera_x, camera_y, rotation, light in values:
                self.assertGreater(abs(camera_x), 8)
                self.assertGreater(abs(camera_y), 6)
                self.assertGreater(abs(rotation), 0.5)
                self.assertGreaterEqual(light, 0.0)
                self.assertLessEqual(light, 1.0)

    def test_emotion_parallax_scales_by_depth(self):
        camera = _emotion_camera(0.55, 1)
        offsets = [_emotion_parallax(depth, camera) for depth in EMOTION_MOTION_STYLE["parallax_depths"]]

        self.assertEqual(len(offsets), 3)
        self.assertEqual(len(set(offsets)), 3)
        self.assertLess(abs(offsets[0][0]), abs(offsets[2][0]))
        self.assertLess(abs(offsets[0][1]), abs(offsets[2][1]))

    def test_emotion_stage_changes_continuously_and_by_variant(self):
        size = (720, 1280)
        first = _emotion_stage(size, 0.25, 0)
        second = _emotion_stage(size, 0.55, 0)
        variant = _emotion_stage(size, 0.25, 2)

        self.assertEqual(first.size, size)
        self.assertEqual(first.mode, "RGBA")
        self.assertIsNotNone(first.getbbox())
        self.assertNotEqual(first.tobytes(), second.tobytes())
        self.assertNotEqual(first.tobytes(), variant.tobytes())

    def test_video_uses_remotion_ui_design_system(self):
        self.assertEqual(REMOTION_UI_STYLE["background"], (248, 250, 252))
        self.assertEqual(REMOTION_UI_STYLE["surface"], (255, 255, 255))
        self.assertEqual(REMOTION_UI_STYLE["text"], (0, 0, 0))
        self.assertEqual(REMOTION_UI_STYLE["primary"], (53, 120, 229))
        self.assertEqual(REMOTION_UI_STYLE["brand"], (11, 132, 243))
        self.assertEqual(REMOTION_UI_STYLE["border"], (0, 0, 0))
        self.assertEqual(REMOTION_UI_STYLE["border_width"], 6)
        self.assertEqual(REMOTION_UI_STYLE["bottom_border_width"], 10)
        self.assertEqual(REMOTION_UI_STYLE["card_radius"], 16)

    def test_emotion_stage_contains_remotion_ui_fingerprint(self):
        stage = _emotion_stage((720, 1280), 0.42, 1)
        colors = {item[:3] for count, item in stage.getcolors(maxcolors=100000)}

        self.assertIn(REMOTION_UI_STYLE["text"], colors)
        self.assertIn(REMOTION_UI_STYLE["brand"], colors)
        self.assertIn(REMOTION_UI_STYLE["primary"], colors)

    def test_motion_tokens_follow_emil_animation_skill(self):
        self.assertEqual(MOTION_TOKENS["ease_out_strong"], (0.23, 1.0, 0.32, 1.0))
        self.assertEqual(MOTION_TOKENS["ease_in_out_strong"], (0.77, 0.0, 0.175, 1.0))
        self.assertEqual(MOTION_TOKENS["enter_duration_seconds"], 0.2)
        self.assertEqual(MOTION_TOKENS["on_screen_duration_seconds"], 0.35)
        self.assertEqual(MOTION_TOKENS["stagger_seconds"], 0.05)

    def test_strong_easing_curves_are_smooth_and_monotonic(self):
        for easing in (ease_out_strong, ease_in_out_strong):
            values = [easing(value / 20) for value in range(21)]
            self.assertEqual(values[0], 0.0)
            self.assertEqual(values[-1], 1.0)
            self.assertEqual(values, sorted(values))

        self.assertGreater(ease_out_strong(0.25), 0.5)
        self.assertGreater(ease_in_out_strong(0.5), 0.5)
        self.assertLess(ease_in_out_strong(0.5), 0.65)

    def test_stagger_step_uses_absolute_time_not_scene_percentage(self):
        self.assertAlmostEqual(stagger_step(10.0), 0.005)
        self.assertAlmostEqual(stagger_step(20.0), 0.0025)
        self.assertEqual(stagger_step(0.0), 0.0)

    def test_roundup_first_three_seconds_use_concrete_hook(self):
        articles = [
            {
                "title": "Judul Khusus Nomor 1",
                "summary": "Isi berita satu.",
                "content": "Latar belakang berita satu menjelaskan kondisi awal. Fakta utama menjelaskan dampak langsung. Tindak lanjut mencakup pemantauan dan evaluasi.",
                "source": "Antara Kaltim",
                "url": "https://example.test/1",
            },
            {
                "title": "Judul Khusus Nomor 2",
                "summary": "Isi berita dua.",
                "source": "Antara Kaltim",
                "url": "https://example.test/2",
            },
            {
                "title": "Judul Khusus Nomor 3",
                "summary": "Isi berita tiga.",
                "source": "Antara Kaltim",
                "url": "https://example.test/3",
            },
        ]

        plan = build_news_roundup_plan(articles, duration_seconds=60)
        opening = plan.scenes[0]

        self.assertTrue(opening.hook)
        self.assertLessEqual(len(opening.hook), 80)
        self.assertGreater(len(opening.hook), 24)
        self.assertNotIn("Judul Khusus Nomor 1", opening.hook)
        self.assertTrue(opening.narration.startswith(opening.hook))
        self.assertEqual(opening.narration[len(opening.hook):len(opening.hook) + 1], " ")

    def test_hook_overlay_is_limited_to_first_three_seconds(self):
        scene = build_video_plan(
            {"title": "Judul berita", "source": "Antara Kaltim", "url": "https://example.test"},
            conclusion="Kesimpulan berita.",
        ).scenes[0]
        hooked_scene = Scene(
            index=scene.index,
            start=scene.start,
            end=scene.end,
            duration=scene.duration,
            heading=scene.heading,
            narration=scene.narration,
            caption=scene.caption,
            layout=scene.layout,
            title=scene.title,
            source=scene.source,
            hook="Tiga kabar Kaltim hari ini bisa mengubah rencanamu.",
        )

        self.assertEqual(
            hook_for_frame(hooked_scene, 1.5, scene.duration),
            "Tiga kabar Kaltim hari ini bisa mengubah rencanamu.",
        )
        self.assertEqual(hook_for_frame(hooked_scene, 3.1, scene.duration), "")
        self.assertEqual(hook_for_frame(hooked_scene, 0.0, scene.duration), hooked_scene.hook)

    def test_cli_plan_uses_sixty_second_full_discussion(self):
        articles = [
            {
                "title": f"Berita Kaltim {index}",
                "summary": "Ringkasan awal.",
                "content": "Latar belakang lengkap menjelaskan kondisi awal, pihak yang terlibat, dan alasan peristiwa ini penting. Fakta utama menjelaskan dampak langsung bagi masyarakat. Tindak lanjut mencakup pemantauan lapangan, koordinasi lintas instansi, layanan alternatif, dan evaluasi berkala.",
                "source": "Tribun Kaltim",
                "url": f"https://example.test/{index}",
            }
            for index in range(1, 4)
        ]

        plan = build_roundup_plan(articles)

        self.assertEqual(plan.duration_seconds, 60)
        self.assertEqual(len(plan.scenes), 7)
        self.assertIn("Latar belakang lengkap", plan.scenes[1].narration)

    def test_adjust_plan_to_audio_removes_silent_gaps(self):
        articles = [
            {"title": f"Berita {index}", "summary": "Isi.", "source": "Antara Kaltim", "url": "x"}
            for index in range(1, 4)
        ]
        plan = build_news_roundup_plan(articles)

        adjusted = adjust_plan_to_audio(
            plan,
            [5.0, 8.0, 5.0, 8.0, 5.0, 8.0, 7.0],
            tail_seconds=0.35,
        )

        self.assertEqual(
            [round(scene.duration, 2) for scene in adjusted.scenes],
            [5.35, 8.35, 5.35, 8.35, 5.35, 8.35, 7.35],
        )
        self.assertEqual(
            [round(scene.start, 2) for scene in adjusted.scenes],
            [0.0, 5.35, 13.7, 19.05, 27.4, 32.75, 41.1],
        )
        self.assertEqual(round(adjusted.scenes[-1].end, 2), 48.45)
        self.assertEqual(round(adjusted.duration_seconds, 2), 48.45)


if __name__ == "__main__":
    unittest.main()
