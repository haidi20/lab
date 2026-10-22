from __future__ import annotations

import unittest
from pathlib import Path


class ModuleConsolidationTests(unittest.TestCase):
    def test_legacy_video_modules_are_removed(self) -> None:
        module_root = Path(__file__).resolve().parents[1]

        self.assertFalse((module_root / 'video_generator').exists())
        self.assertFalse((module_root / 'video_producer').exists())

    def test_video_pipeline_api_is_exposed_by_ui_animation(self) -> None:
        from modules.ui_animation import (
            FakeKlingBackend,
            KlingBackend,
            VideoGenerator,
            VideoRequest,
            VideoResult,
            VideoTask,
            build_news_roundup_plan,
            enrich_articles,
            render_article_video,
        )

        backend = FakeKlingBackend()
        generator = VideoGenerator(backend=backend, api_key='test-key')
        request = VideoRequest(prompt='Kucing oren bermain di taman')

        task = generator.submit(request)
        result = generator.wait_for_result(task.task_id)

        self.assertEqual(backend.last_request, request)
        self.assertEqual(result.status, 'completed')
        self.assertTrue(result.video_url.startswith('https://'))
        self.assertTrue(callable(build_news_roundup_plan))
        self.assertTrue(callable(enrich_articles))
        self.assertTrue(callable(render_article_video))
