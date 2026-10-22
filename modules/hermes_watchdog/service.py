from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class WatchdogResult:
    status: str
    action: str
    detail: str

    def message(self) -> str:
        return 'Hermes Watchdog' + os.linesep + self.detail


@dataclass
class WatchdogState:
    git_fingerprint: str | None = None
    last_progress_at: str | None = None
    last_prune_at: str | None = None
    nudge_count: int = 0
    restart_count: int = 0


class HermesWatchdog:
    def __init__(
        self,
        cron_reader: Callable[[], dict[str, object]],
        log_path: Path,
        git_status_reader: Callable[[], str],
        command_runner: Callable[[list[str], float], object] | None = None,
        notifier: Callable[[str], None] | None = None,
        now: Callable[[], datetime] | None = None,
        state_path: Path | None = None,
        stale_minutes: float = 15.0,
        job_id: str = '442bba7081d8',
        hermes_binary: str = 'hermes',
        command_timeout: float = 120.0,
        prune_interval_minutes: float = 360.0,
        prune_older_than: str = '1d',
    ) -> None:
        self.cron_reader = cron_reader
        self.log_path = log_path
        self.git_status_reader = git_status_reader
        self.command_runner = command_runner
        self.notifier = notifier
        self.now = now or datetime.now
        self.state_path = state_path
        self.stale_minutes = stale_minutes
        self.job_id = job_id
        self.hermes_binary = hermes_binary
        self.command_timeout = command_timeout
        self.prune_interval_minutes = prune_interval_minutes
        self.prune_older_than = prune_older_than
        self.state = self._load_state()

    def check(self) -> WatchdogResult:
        job = self._job()
        git_status = self.git_status_reader()
        progress_at = self._progress_at(job, git_status)
        current = self.now()
        self.state.git_fingerprint = git_status
        self.state.last_progress_at = progress_at.isoformat()

        if job is None:
            result = WatchdogResult('missing_job', 'none', 'Job Hermes tidak ditemukan.')
        elif job.get('enabled') is False:
            result = self._resume_job()
        elif self._age_minutes(current, progress_at) < self.stale_minutes:
            self.state.nudge_count = 0
            result = WatchdogResult('healthy', 'none', 'Worker Hermes masih bergerak.')
        elif self.state.nudge_count == 0:
            self.state.nudge_count = 1
            result = WatchdogResult(
                'stale',
                'notify',
                'Worker Hermes stale tanpa patch atau perubahan git.',
            )
        else:
            result = self._restart_gateway()

        self._prune_sessions()
        self._save_state()
        if result.action != 'none' and self.notifier is not None:
            self.notifier(result.message())
        return result

    def _job(self) -> dict[str, object] | None:
        payload = self.cron_reader()
        jobs = payload.get('jobs', [])
        if not isinstance(jobs, list):
            return None
        for candidate in jobs:
            if isinstance(candidate, dict) and candidate.get('id') == self.job_id:
                return candidate
        return None

    def _progress_at(self, job: dict[str, object] | None, git_status: str) -> datetime:
        current = self.now()
        if self.state.git_fingerprint is None and git_status:
            return current

        if self.state.git_fingerprint is not None and self.state.git_fingerprint != git_status:
            return current

        candidates = [self._log_progress_at()]
        if job is not None:
            candidates.append(self._parse_datetime(job.get('last_run_at')))
        stored = self._parse_datetime(self.state.last_progress_at)
        if stored is not None:
            candidates.append(stored)
        valid = [candidate for candidate in candidates if candidate is not None]
        return max(valid) if valid else current

    def _log_progress_at(self) -> datetime | None:
        if not self.log_path.exists():
            return None
        try:
            with self.log_path.open('rb') as handle:
                handle.seek(0, os.SEEK_END)
                size = handle.tell()
                handle.seek(max(0, size - 262144))
                content = handle.read().decode('utf-8', errors='replace')
        except OSError:
            return None

        markers = (
            'tool patch completed',
            'tool write_file completed',
            'cron.scheduler: Job',
        )
        latest: datetime | None = None
        for line in content.splitlines():
            if not any(marker in line for marker in markers):
                continue
            match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+)', line)
            if match is None:
                continue
            try:
                timestamp = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S,%f')
            except ValueError:
                continue
            if latest is None or timestamp > latest:
                latest = timestamp
        return latest

    def _resume_job(self) -> WatchdogResult:
        commands = [
            [self.hermes_binary, 'cron', 'resume', self.job_id],
            [self.hermes_binary, 'cron', 'run', self.job_id],
        ]
        errors = self._run_commands(commands)
        detail = 'Job Hermes paused; watchdog resume dan trigger ulang.'
        if errors:
            detail += ' Perintah gagal: ' + '; '.join(errors)
        return WatchdogResult('paused', 'resume_job', detail)

    def _restart_gateway(self) -> WatchdogResult:
        command = [self.hermes_binary, 'gateway', 'restart', '--yes']
        errors = self._run_commands([command])
        self.state.nudge_count = 0
        self.state.restart_count += 1
        detail = 'Worker Hermes stale berulang; gateway direstart.'
        if errors:
            detail += ' Perintah gagal: ' + '; '.join(errors)
        return WatchdogResult('stale', 'restart_gateway', detail)

    def _prune_sessions(self) -> None:
        current = self.now()
        last_prune_at = self._parse_datetime(self.state.last_prune_at)
        if last_prune_at is not None:
            age_minutes = self._age_minutes(current, last_prune_at)
            if age_minutes < self.prune_interval_minutes:
                return

        command = [
            self.hermes_binary,
            'sessions',
            'prune',
            '--older-than',
            self.prune_older_than,
            '--yes',
        ]
        errors = self._run_commands([command])
        if not errors:
            self.state.last_prune_at = current.isoformat()

    def _run_commands(self, commands: list[list[str]]) -> list[str]:
        if self.command_runner is None:
            return []
        errors: list[str] = []
        for command in commands:
            try:
                completed = self.command_runner(command, self.command_timeout)
                if int(getattr(completed, 'returncode', 1)) != 0:
                    text = str(getattr(completed, 'stderr', '') or getattr(completed, 'stdout', '') or command)
                    errors.append(text.strip()[:300])
            except Exception as error:
                errors.append(str(error)[:300])
        return errors

    def _load_state(self) -> WatchdogState:
        if self.state_path is None or not self.state_path.exists():
            return WatchdogState()
        try:
            payload = json.loads(self.state_path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return WatchdogState()
        return WatchdogState(
            git_fingerprint=payload.get('git_fingerprint'),
            last_progress_at=payload.get('last_progress_at'),
            last_prune_at=payload.get('last_prune_at'),
            nudge_count=int(payload.get('nudge_count', 0)),
            restart_count=int(payload.get('restart_count', 0)),
        )

    def _save_state(self) -> None:
        if self.state_path is None:
            return
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.state_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(asdict(self.state), indent=2), encoding='utf-8')
        temporary.replace(self.state_path)

    @staticmethod
    def _parse_datetime(value: object) -> datetime | None:
        if not isinstance(value, str) or not value:
            return None
        try:
            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return None
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone().replace(tzinfo=None)
        return parsed

    @staticmethod
    def _age_minutes(current: datetime, previous: datetime) -> float:
        return max(0.0, (current - previous).total_seconds() / 60.0)
