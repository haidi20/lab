import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class VideoRequest:
    prompt: str
    mode: str = "std"
    duration: str = "5"
    aspect_ratio: str = "9:16"
    negative_prompt: str = ""


@dataclass(frozen=True)
class VideoTask:
    task_id: str
    status: str = "submitted"


@dataclass(frozen=True)
class VideoResult:
    task_id: str
    status: str
    video_url: str = ""


class FakeKlingBackend:
    def __init__(self) -> None:
        self.last_request: VideoRequest | None = None
        self._tasks: dict[str, str] = {}

    def submit_task(self, request: VideoRequest, api_key: str) -> str:
        self.last_request = request
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        self._tasks[task_id] = "completed"
        return task_id

    def get_task(self, task_id: str, api_key: str) -> VideoResult:
        status = self._tasks.get(task_id, "failed")
        return VideoResult(
            task_id=task_id,
            status=status,
            video_url=f"https://cdn.example/kling/{task_id}.mp4" if status == "completed" else "",
        )


class KlingBackend:
    BASE_URL = "https://api.klingai.com/v1"

    def __init__(self, timeout_seconds: int = 30) -> None:
        self._timeout = timeout_seconds

    def submit_task(self, request: VideoRequest, api_key: str) -> str:
        import json
        from urllib.request import Request, urlopen

        payload = {
            "prompt": request.prompt,
            "mode": request.mode,
            "duration": request.duration,
            "aspect_ratio": request.aspect_ratio,
        }
        if request.negative_prompt:
            payload["negative_prompt"] = request.negative_prompt
        req = Request(
            f"{self.BASE_URL}/videos/text2video",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with urlopen(req, timeout=self._timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data["data"]["task_id"]

    def get_task(self, task_id: str, api_key: str) -> VideoResult:
        import json
        from urllib.request import Request, urlopen

        req = Request(
            f"{self.BASE_URL}/videos/text2video/{task_id}",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        with urlopen(req, timeout=self._timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        task_data = data["data"]["task_result"]
        status = data["data"]["task_status"]
        videos = task_data.get("videos", []) if task_data else []
        video_url = videos[0]["url"] if videos else ""
        return VideoResult(task_id=task_id, status=status, video_url=video_url)


class VideoGenerator:
    def __init__(self, backend: Any, api_key: str, poll_interval: int = 5, max_wait: int = 600) -> None:
        self._backend = backend
        self._api_key = api_key
        self._poll_interval = poll_interval
        self._max_wait = max_wait

    def submit(self, request: VideoRequest) -> VideoTask:
        task_id = self._backend.submit_task(request, self._api_key)
        return VideoTask(task_id=task_id)

    def get_status(self, task_id: str) -> VideoResult:
        return self._backend.get_task(task_id, self._api_key)

    def wait_for_result(self, task_id: str) -> VideoResult:
        deadline = time.monotonic() + self._max_wait
        while time.monotonic() < deadline:
            result = self.get_status(task_id)
            if result.status in ("completed", "failed"):
                return result
            time.sleep(self._poll_interval)
        return VideoResult(task_id=task_id, status="timeout")
