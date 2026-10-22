import unittest
from pathlib import Path
import tempfile

from modules.ui_animation.producer import build_video_plan
from modules.remotion_video.converter import plan_to_remotion_props
from modules.remotion_video.pipeline import (
    resolve_executable,
    build_render_command,
    build_remotion_payload,
    prepare_remotion_project,
)


class RemotionVideoTests(unittest.TestCase):
    def setUp(self):
        self.plan = build_video_plan(
            {
                "title": "Judul berita",
                "source": "Antara Kaltim",
                "url": "https://example.test",
                "summary": "Latar belakang menjelaskan kondisi awal. Fakta utama menjelaskan dampak langsung.",
            },
            duration_seconds=30,
        )

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
