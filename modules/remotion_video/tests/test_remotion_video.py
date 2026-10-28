import unittest
import unittest.mock
from pathlib import Path
import re
import tempfile

from modules.ui_animation.producer import build_video_plan
from modules.remotion_video.converter import plan_to_remotion_props
from modules.remotion_video.pipeline import (
    resolve_executable,
    build_render_command,
    build_still_command,
    build_remotion_payload,
    prepare_remotion_project,
)
from modules.remotion_video.converter import articles_to_cover_props
from modules.remotion_video import cli
from modules.remotion_video import cli


class RemotionVideoTests(unittest.TestCase):
    def setUp(self):
        self.component_source = (
            Path(__file__).parents[1]
            / "remotion"
            / "src"
            / "KaltimRoundup.tsx"
        ).read_text(encoding="utf-8")
        self.root_source = (
            Path(__file__).parents[1]
            / "remotion"
            / "src"
            / "Root.tsx"
        ).read_text(encoding="utf-8")
        self.cover_source = (
            Path(__file__).parents[1]
            / "remotion"
            / "src"
            / "KaltimCover.tsx"
        ).read_text(encoding="utf-8")
        self.plan = build_video_plan(
            {
                "title": "Judul berita",
                "source": "Antara Kaltim",
                "url": "https://example.test",
                "summary": "Latar belakang menjelaskan kondisi awal. Fakta utama menjelaskan dampak langsung.",
            },
            duration_seconds=30,
        )

    def test_video_component_uses_reference_dark_design_system(self):
        legacy_tokens = (
            "#F8FAFC", "#FFFFFF", "#000000", "#666666",
            "#3578E5", "#0B84F3", "#E2E8F0",
        )
        reference_tokens = (
            "#0B1323", "#0D1729", "#F5FAFF", "#A3E635", "#F59E0B",
        )
        for token in legacy_tokens:
            self.assertNotIn(token, self.component_source)
        for token in reference_tokens:
            self.assertIn(token, self.component_source)
        self.assertNotIn("Scene x/y", self.component_source)

    def test_video_component_uses_reference_geometric_font(self):
        self.assertIn("fontFamily: 'Poppins", self.component_source)

    def test_root_loads_reference_font_before_render(self):
        self.assertIn("@remotion/google-fonts/Poppins", self.root_source)
        self.assertIn("loadFont", self.root_source)

    def test_cover_component_uses_reference_dark_design_system(self):
        for token in ("white", "#91EAE4", "#86A8E7", "#000000"):
            self.assertNotIn(token, self.cover_source)
        for token in ("#0B1323", "#F5FAFF", "#A3E635", "#F59E0B", "Poppins"):
            self.assertIn(token, self.cover_source)

    def test_video_component_keeps_hook_overlay_to_three_seconds(self):
        self.assertIn("Boolean(scene.hook) && frame < fps * 3", self.component_source)
        self.assertIn("[fps * 3 - 8, fps * 3]", self.component_source)

    def test_video_component_uses_vertical_space_for_discussion(self):
        self.assertIn("flex: '0 1 880px'", self.component_source)
        self.assertIn("justifyContent: 'space-evenly'", self.component_source)

    def test_video_component_has_layout_motifs_and_continuous_motion(self):
        for layout in ("headline", "detail", "metrics", "process", "conclusion"):
            self.assertIn(layout, self.component_source)
        for motion_marker in ("Math.sin", "Math.cos", "frame *", "spring("):
            self.assertIn(motion_marker, self.component_source)

    def test_video_component_uses_interactive_topic_chips(self):
        self.assertIn("const TopicChips", self.component_source)
        self.assertIn("topicKeywords", self.component_source)
        self.assertIn("chipReveal", self.component_source)

    def test_video_component_highlights_caption_phrases_with_audio_aware_timing(self):
        self.assertIn("const HighlightedCaption", self.component_source)
        self.assertIn("phraseProgress", self.component_source)
        self.assertIn("colors.primary", self.component_source)

    def test_video_component_varies_accent_and_motif_by_layout(self):
        self.assertIn("const layoutAccents", self.component_source)
        self.assertIn("const layoutMotifs", self.component_source)
        self.assertIn("scene.layout", self.component_source)

    def test_video_component_hides_news_counter_and_source_label(self):
        self.assertNotIn("scene.heading", self.component_source)
        self.assertNotIn("Sumber:", self.component_source)
        self.assertNotIn("Berita 2/3", self.component_source)
        self.assertIn("globalProgress", self.component_source)
        self.assertNotIn("Scene {scene.index}", self.component_source)

    def test_video_component_dubs_every_scene_with_remotion_audio(self):
        self.assertIn("<Audio", self.component_source)
        self.assertIn("staticFile(scene.audioPath)", self.component_source)

    def test_cli_uses_short_discussion_duration(self):
        with unittest.mock.patch.object(cli.sys, "argv", ["cli.py", "--duration", "60"]):
            args = cli.parse_args()

        self.assertEqual(args.duration, 60)

    def test_cli_supports_single_news_limit(self):
        with unittest.mock.patch.object(cli.sys, "argv", ["cli.py", "--limit", "1"]):
            args = cli.parse_args()

        self.assertEqual(args.limit, 1)

    def test_plan_converts_to_vertical_remotion_props(self):
        props = plan_to_remotion_props(self.plan, fps=24)

        self.assertEqual(props["width"], 1080)
        self.assertEqual(props["height"], 1920)
        self.assertEqual(props["fps"], 24)
        self.assertEqual(len(props["scenes"]), 4)
        self.assertEqual(
            props["durationInFrames"],
            sum(scene["durationInFrames"] for scene in props["scenes"]),
        )
        self.assertTrue(all(scene["audioPath"].startswith("audio/scene_") for scene in props["scenes"]))
        self.assertTrue(props["scenes"][0]["hook"])
        self.assertFalse(any(scene["hook"] for scene in props["scenes"][1:]))

    def test_payload_syncs_scenes_to_audio_durations(self):
        synced_plan, props = build_remotion_payload(
            self.plan,
            audio_durations=[6.0, 5.0, 7.0, 4.0],
        )

        self.assertEqual(len(synced_plan.scenes), 4)
        self.assertAlmostEqual(synced_plan.scenes[0].duration, 6.35)
        self.assertAlmostEqual(synced_plan.scenes[1].duration, 5.35)
        self.assertEqual(props["fps"], 24)
        self.assertEqual(len(props["scenes"]), 4)
        self.assertGreater(props["durationInFrames"], 500)

    def test_render_command_uses_local_remotion_project(self):
        command = build_render_command(
            props_path="build/props.json",
            output_path="public/generated_video/remotion.mp4",
        )

        self.assertTrue(str(command[0]).lower().endswith("bunx.cmd"))
        self.assertIn("render", command)
        self.assertIn("KaltimRoundup", command)
        self.assertTrue(any(str(value).endswith("props.json") for value in command))
        self.assertTrue(any(str(value).endswith("remotion.mp4") for value in command))

    def test_articles_convert_to_cover_props(self):
        articles = [
            {"title": f"Berita {index}", "source": "Tribun Kaltim"}
            for index in range(1, 4)
        ]

        props = articles_to_cover_props(articles)

        self.assertEqual(props["width"], 1080)
        self.assertEqual(props["height"], 1350)
        self.assertEqual(props["title"], "3 Berita Terbaru Kaltim")
        self.assertEqual(len(props["articles"]), 3)
        self.assertEqual(props["articles"][0]["title"], "Berita 1")

    def test_still_command_uses_cover_composition(self):
        command = build_still_command(
            props_path="build/cover.json",
            output_path="public/generated_images/kaltim.png",
        )

        self.assertIn("still", command)
        self.assertIn("KaltimCover", command)
        self.assertIn("--frame=150", command)
        self.assertTrue(any(str(value).endswith("kaltim.png") for value in command))
        self.assertTrue(any(str(value).endswith("cover.json") for value in command))

    def test_resolve_executable_finds_windows_bunx(self):
        executable = resolve_executable("bunx")
        self.assertIsNotNone(executable)
        self.assertTrue(Path(str(executable)).exists())

    def test_prepare_remotion_project_copies_audio_and_writes_props(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            build_dir = root / "build"
            project_dir = root / "remotion"
            build_dir.mkdir()
            audio_paths = []
            for index in range(1, 5):
                audio_path = build_dir / f"scene_{index:02d}.mp3"
                audio_path.write_bytes(b"fake-audio")
                audio_paths.append(audio_path)

            props_path = prepare_remotion_project(
                self.plan,
                audio_paths=audio_paths,
                audio_durations=[6.0, 5.0, 7.0, 4.0],
                build_dir=build_dir,
                project_dir=project_dir,
            )

            self.assertEqual(props_path, build_dir / "props.json")
            self.assertTrue(props_path.exists())
            for index in range(1, 5):
                copied = project_dir / "public" / "audio" / f"scene_{index:02d}.mp3"
                self.assertTrue(copied.exists())
