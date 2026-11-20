from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from modules.inaproc.api.auth import AuthError
from modules.inaproc.api.db import DbUnavailableError
from modules.inaproc.api.spt import SptNumber, sequence_range


def utc_now_naive() -> datetime:
    """Store timestamps as naive UTC so MySQL DATETIME stays unambiguous."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def local_iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


@dataclass
class JobState:
    job_id: str | None = None
    total: int = 0
    found: int = 0
    empty: int = 0
    errors: int = 0
    skipped: int = 0
    status: str = "idle"
    start: int | None = None
    end: int | None = None
    template: str | None = None
    last_error: str | None = None
    current: str | None = None
    started_at: str | None = None
    finished_at: str | None = None

    @property
    def done(self) -> int:
        """Plan invariant: done = found + empty + error."""
        return self.found + self.empty + self.errors

    @property
    def processed(self) -> int:
        return self.done + self.skipped

    @property
    def progress(self) -> float:
        if not self.total:
            return 0.0
        return round(self.processed / self.total, 4)

    def as_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "nomor": self.template,
            "template": self.template,
            "start": self.start,
            "end": self.end,
            "total": self.total,
            "done": self.done,
            "processed": self.processed,
            "found": self.found,
            "empty": self.empty,
            "error": self.errors,
            "errors": self.errors,
            "skipped": self.skipped,
            "progress": self.progress,
            "current_number": self.current,
            "current": self.current,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "last_error": self.last_error,
        }


class Collector:
    def __init__(
        self,
        store,
        scraper,
        *,
        sleep: Callable[[float], None] = time.sleep,
        delay_min: float = 1.0,
        delay_max: float = 3.0,
        max_retries: int = 2,
    ) -> None:
        self.store = store
        self.scraper = scraper
        self._sleep = sleep
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.max_retries = max_retries
        self._cancel = threading.Event()
        self.job = JobState()

    def cancel(self) -> None:
        self._cancel.set()
        if self.job.status == "running":
            self.job.status = "cancelling"

    def collect(
        self,
        template: SptNumber,
        start: int,
        end: int,
        *,
        force: bool = False,
    ) -> JobState:
        if self.job.status not in {"running", "cancelling"} or self.job.total == 0:
            self.prepare(template, start, end)
        numbers = sequence_range(template, start, end)
        # A cancel that arrives before the worker starts must not be lost.
        cancelled_before_start = self._cancel.is_set()
        self._cancel.clear()
        self.job.status = "running"
        self.job.started_at = local_iso_now()
        try:
            for spt in numbers:
                if cancelled_before_start or self._cancel.is_set():
                    self.job.status = "cancelled"
                    self.job.current = None
                    self.job.finished_at = local_iso_now()
                    return self.job
                self.job.current = str(spt)
                if not force and self._should_skip(str(spt)):
                    self.job.skipped += 1
                    continue
                self._process(spt)
                if self.job.status in {"failed", "stopped"}:
                    self.job.status = "failed"
                    self.job.current = None
                    self.job.finished_at = local_iso_now()
                    return self.job
                if self.job.processed < self.job.total:
                    self._sleep(random.uniform(self.delay_min, self.delay_max))
            self.job.status = "done"
        except DbUnavailableError as exc:
            self.job.status = "failed"
            self.job.last_error = f"db_unavailable: {exc}"
        finally:
            self.job.current = None
            if self.job.finished_at is None:
                self.job.finished_at = local_iso_now()
        return self.job

    def prepare(self, template: SptNumber, start: int, end: int) -> JobState:
        """Create the job state synchronously so the API can respond accurately."""
        numbers = sequence_range(template, start, end)
        self.job = JobState(
            job_id=datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:-3],
            total=len(numbers),
            status="running",
            start=start,
            end=end,
            template=str(template),
            started_at=local_iso_now(),
        )
        return self.job

    def _process(self, spt: SptNumber) -> None:
        number = str(spt)
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                result = self.scraper.fetch(spt)
                now = utc_now_naive()
                if result.status == "found":
                    self._save_found(number, result.rows, now)
                    self.job.found += 1
                else:
                    self._save_empty(number, now)
                    self.job.empty += 1
                return
            except DbUnavailableError:
                raise
            except AuthError as exc:
                error = f"belum_login: {exc}"
                self.store.upsert_check(number, "error", error, utc_now_naive())
                self.job.errors += 1
                self.job.last_error = error
                self.job.status = "failed"
                return
            except Exception as exc:
                last_error = str(exc)
                if attempt < self.max_retries:
                    self._sleep((2**attempt) + random.uniform(0, 0.5))
        self.store.upsert_check(number, "error", last_error, utc_now_naive())
        self.job.errors += 1
        self.job.last_error = last_error

    def _should_skip(self, number: str) -> bool:
        """Use the store's consistency-aware check when it is available."""
        resolver = getattr(self.store, "should_skip", None)
        if callable(resolver):
            return bool(resolver(number))
        return bool(self.store.is_final(number))

    def _save_found(self, number: str, rows, now: datetime) -> None:
        save = getattr(self.store, "save_found", None)
        if callable(save):
            save(number, rows, now)
            return
        self.store.upsert_rows(number, rows, now)
        self.store.upsert_check(number, "found", None, now)

    def _save_empty(self, number: str, now: datetime) -> None:
        save = getattr(self.store, "save_empty", None)
        if callable(save):
            save(number, now)
            return
        self.store.delete_rows_for_number(number)
        self.store.upsert_check(number, "empty", None, now)
