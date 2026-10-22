from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Callable
from urllib.parse import quote, urlencode


class HermesStatusProvider:
    def __init__(
        self,
        trello_fetch: Callable[[str], object],
        trello_key: str,
        trello_token: str,
        progress_list_id: str,
        jobs_path: Path | None = None,
        delegation_root: Path | None = None,
        agent_log_path: Path | None = None,
    ) -> None:
        self.trello_fetch = trello_fetch
        self.trello_key = trello_key
        self.trello_token = trello_token
        self.progress_list_id = progress_list_id
        self.jobs_path = jobs_path
        self.delegation_root = delegation_root
        self.agent_log_path = agent_log_path

    def summary(self) -> str:
        try:
            cards = self._progress_cards()
        except Exception as error:
            return os.linesep.join(
                [
                    'Status Hermes',
                    'Status Hermes belum tersedia.',
                    f'Penyebab: {error}',
                ]
            )

        lines = ['Status Hermes', '']
        if not cards:
            lines.append('Tidak ada kartu di progress.')
        else:
            lines.append(f'Kartu aktif: {len(cards)}')
            lines.append('')

        for index, card in enumerate(cards, start=1):
            card_name = card.get('name', 'Kartu tanpa nama')
            lines.append(f'{index}. {card_name}')
            for checklist in card.get('checklists', []):
                for item in checklist.get('checkItems', []):
                    mark = '[x]' if item.get('state') == 'complete' else '[ ]'
                    item_name = item.get('name', 'Checklist tanpa nama')
                    lines.append(f'   {mark} {item_name}')
            lines.append('')

        lines.extend(self._delegation_lines())
        lines.extend(self._agent_activity_lines())
        lines.extend(self._job_lines())
        return self._limited(os.linesep.join(lines))

    def _progress_cards(self) -> list[dict[str, object]]:
        response = self.trello_fetch(self._trello_url())
        if not isinstance(response, list):
            raise ValueError('Respons Trello tidak valid')
        return [card for card in response if isinstance(card, dict)]

    def _delegation_lines(self) -> list[str]:
        if self.delegation_root is None or not self.delegation_root.exists():
            return []

        try:
            manifests = sorted(
                self.delegation_root.glob('*/manifest.json'),
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )
        except OSError:
            return []

        lines: list[str] = []
        for manifest_path in manifests:
            try:
                payload = json.loads(manifest_path.read_text(encoding='utf-8'))
            except (OSError, ValueError):
                continue
            tasks = payload.get('tasks', [])
            if not isinstance(tasks, list):
                continue
            for task in tasks:
                if not isinstance(task, dict) or task.get('status') != 'running':
                    continue
                goal = str(task.get('goal', 'Aktivitas Hermes'))
                lines.extend(
                    [
                        '',
                        'Aktivitas Hermes',
                        f'Tugas: {self._short(goal, 240)}',
                        'Status: running',
                    ]
                )
                log_tail = self._read_log_tail(task.get('log'))
                if log_tail:
                    lines.append(f'Log terakhir: {self._short(log_tail, 500)}')
                for activity in self._delegation_activities(task.get('log')):
                    lines.append(activity)
        return lines

    def _agent_activity_lines(self) -> list[str]:
        if self.agent_log_path is None or not self.agent_log_path.exists():
            return []

        relevant = [
            line
            for line in self._read_log_lines(self.agent_log_path, byte_limit=4000, line_limit=20)
            if ' INFO ' in line and ('agent.codex_runtime' in line or 'agent.conversation_loop' in line or 'agent.tool_executor' in line)
        ][-5:]
        if not relevant:
            return []

        lines = ['', 'Proses Hermes']
        for line in relevant:
            timestamp_match = re.match(r'^\d{4}-\d{2}-\d{2} (\d{2}:\d{2}:\d{2})', line)
            timestamp = timestamp_match.group(1) if timestamp_match else ''
            message = line.split(': ', 1)[-1]
            if 'agent.tool_executor' in line:
                category = 'Proses'
            else:
                category = 'Berpikir'
            call_match = re.search(r'API call #\d+', message)
            if call_match:
                message = call_match.group(0)
            lines.append(f'{timestamp} {category}: {self._short(message, 180)}')
        return lines

    def _delegation_activities(self, value: object) -> list[str]:
        activities: list[str] = []
        for line in self._read_log_lines(value, byte_limit=2000, line_limit=4):
            if '-> terminal(' in line:
                command = line.split('-> terminal(', 1)[-1].rsplit(')', 1)[0]
                activities.append(f'Analisa: {self._short(command, 220)}')
            elif 'result   |' in line or 'result |' in line:
                result = line.split('|', 1)[-1].strip()
                activities.append(f'Proses: {self._short(result, 220)}')
        return activities[-3:]

    @staticmethod
    def _read_log_lines(value: object, byte_limit: int, line_limit: int) -> list[str]:
        log_path = value if isinstance(value, Path) else Path(str(value)) if value else None
        if log_path is None:
            return []
        try:
            with log_path.open('rb') as handle:
                handle.seek(0, os.SEEK_END)
                size = handle.tell()
                handle.seek(max(0, size - byte_limit))
                content = handle.read().decode('utf-8', errors='replace')
        except OSError:
            return []
        return [line.strip() for line in content.splitlines() if line.strip()][-line_limit:]

    @staticmethod
    def _read_log_tail(value: object, byte_limit: int = 1200) -> str:
        lines = HermesStatusProvider._read_log_lines(value, byte_limit=byte_limit, line_limit=1)
        return lines[-1] if lines else ''

    @staticmethod
    def _short(text: object, limit: int) -> str:
        value = str(text).replace(os.linesep, ' ').replace('\n', ' ').strip()
        return value if len(value) <= limit else value[: limit - 3] + '...'

    def _trello_url(self) -> str:
        query = urlencode(
            {
                'key': self.trello_key,
                'token': self.trello_token,
                'fields': 'name,shortUrl',
                'checklists': 'all',
                'checkItem_fields': 'name,state',
            }
        )
        return f'https://api.trello.com/1/lists/{quote(self.progress_list_id)}/cards?{query}'

    def _job_lines(self) -> list[str]:
        if self.jobs_path is None or not self.jobs_path.exists():
            return []

        try:
            payload = json.loads(self.jobs_path.read_text(encoding='utf-8'))
            jobs = payload.get('jobs', [])
        except (OSError, ValueError):
            return ['Status cron Hermes tidak tersedia.']

        lines: list[str] = []
        for job in jobs:
            if not isinstance(job, dict):
                continue
            job_name = job.get('name', 'Job Hermes')
            status = job.get('last_status') or job.get('state') or 'tidak diketahui'
            lines.append('')
            lines.append(f'Worker: {job_name}')
            lines.append(f'Status cron: {status}')
            schedule = job.get('schedule_display')
            if schedule:
                lines.append(f'Jadwal: {schedule}')
            last_run = job.get('last_run_at')
            if last_run:
                lines.append(f'Run terakhir: {last_run}')
            last_error = job.get('last_error')
            if last_error:
                lines.append(f'Alasan: {last_error}')
        return lines

    @staticmethod
    def _limited(text: str, limit: int = 3800) -> str:
        if len(text) <= limit:
            return text
        return text[:limit].rstrip() + os.linesep + '... Pesan dipotong.'
