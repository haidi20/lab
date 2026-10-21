import unittest

from modules.video_generator import (
    FakeKlingBackend,
    VideoGenerator,
    VideoRequest,
)


class TestVideoGenerator(unittest.TestCase):
    def test_submit_returns_task_id(self) -> None:
        backend = FakeKlingBackend()
        generator = VideoGenerator(backend=backend, api_key="test-key")
        request = VideoRequest(prompt="Kucing oren bermain di taman", mode="std", duration="5")

        task = generator.submit(request)

        self.assertTrue(task.task_id.startswith("task_"))

    def test_poll_until_completed(self) -> None:
        backend = FakeKlingBackend()
        generator = VideoGenerator(backend=backend, api_key="test-key")
        request = VideoRequest(prompt="Robot menari", mode="std", duration="5")

        task = generator.submit(request)
        result = generator.wait_for_result(task.task_id)

        self.assertEqual(result.status, "completed")
        self.assertTrue(result.video_url.startswith("https://"))

    def test_backend_receives_request_payload(self) -> None:
        backend = FakeKlingBackend()
        generator = VideoGenerator(backend=backend, api_key="test-key")
        request = VideoRequest(
            prompt="Drone shot pantai",
            mode="pro",
            duration="10",
            aspect_ratio="9:16",
        )

        generator.submit(request)

        self.assertEqual(backend.last_request.prompt, "Drone shot pantai")
        self.assertEqual(backend.last_request.mode, "pro")
        self.assertEqual(backend.last_request.duration, "10")
        self.assertEqual(backend.last_request.aspect_ratio, "9:16")

    def test_negative_prompt_supported(self) -> None:
        backend = FakeKlingBackend()
        generator = VideoGenerator(backend=backend, api_key="test-key")
        request = VideoRequest(
            prompt="Kota futuristik",
            mode="std",
            duration="5",
            negative_prompt="blur, distorsi",
        )

        generator.submit(request)

        self.assertEqual(backend.last_request.negative_prompt, "blur, distorsi")


if __name__ == "__main__":
    unittest.main()
