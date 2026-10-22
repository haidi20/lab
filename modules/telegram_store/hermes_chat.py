from __future__ import annotations

import os
import json
import subprocess
import urllib.request
from pathlib import Path
from typing import Callable

from .hermes_status import HermesStatusProvider


class HermesChatClient:
    def __init__(
        self,
        runner: Callable[[list[str], bytes, float], object],
        hermes_binary: str,
        workdir: Path,
        status_provider: HermesStatusProvider | None = None,
        timeout: float = 180.0,
        provider_post: Callable[[dict[str, object]], object] | None = None,
        provider_model: str = 'cd',
    ) -> None:
        self.runner = runner
        self.hermes_binary = hermes_binary
        self.workdir = workdir
        self.status_provider = status_provider
        self.timeout = timeout
        self.provider_post = provider_post
        self.provider_model = provider_model

    def ask(self, question: str) -> str:
        clean_question = question.strip()
        if not clean_question:
            raise ValueError('Pertanyaan untuk Hermes kosong')

        command = [
            self.hermes_binary,
            'chat',
            '--query-file',
            '-',
            '--quiet',
            '--yolo',
            '--run-budget',
            str(int(self.timeout)),
            '--source',
            'telegram',
            '--in',
            str(self.workdir),
        ]
        try:
            completed = self.runner(command, self._query(clean_question).encode('utf-8'), self.timeout)
        except subprocess.TimeoutExpired as error:
            raise RuntimeError('Hermes tidak menjawab sebelum batas waktu.') from error
        except RuntimeError as error:
            if self.provider_post is not None and self._can_use_provider_fallback(str(error)):
                return self._ask_provider(clean_question)
            raise

        stdout = str(getattr(completed, 'stdout', '') or '')
        stderr = str(getattr(completed, 'stderr', '') or '')
        if int(getattr(completed, 'returncode', 1)) != 0:
            message = stderr.strip() or stdout.strip() or 'Hermes gagal menjawab.'
            if self.provider_post is not None and self._can_use_provider_fallback(message):
                return self._ask_provider(clean_question)
            raise RuntimeError(message)
        answer = stdout.strip()
        if not answer:
            raise RuntimeError('Hermes mengembalikan jawaban kosong.')
        return self._limited(answer)

    def _ask_provider(self, question: str) -> str:
        assert self.provider_post is not None
        payload = {
            'model': self.provider_model,
            'input': self._query(question),
            'stream': False,
        }
        response = self.provider_post(payload)
        answer = self._extract_output_text(response)
        if not answer:
            raise RuntimeError('Provider Hermes mengembalikan jawaban kosong.')
        return self._limited(answer)

    @staticmethod
    def _can_use_provider_fallback(message: str) -> bool:
        lowered = message.lower()
        return 'gateway_other_session' in lowered or 'gateway inaccessible' in lowered

    @staticmethod
    def _extract_output_text(response: object) -> str:
        if not isinstance(response, dict):
            return ''
        output = response.get('output', [])
        if not isinstance(output, list):
            return ''
        for item in output:
            if not isinstance(item, dict) or item.get('type') != 'message':
                continue
            content = item.get('content', [])
            if not isinstance(content, list):
                continue
            for part in content:
                if isinstance(part, dict) and part.get('type') == 'output_text':
                    return str(part.get('text', '')).strip()
        return ''


    def _query(self, question: str) -> str:
        lines = [
            'Kamu dihubungi lewat bot Telegram.',
            'Jawab dalam Bahasa Indonesia dengan ringkas dan langsung.',
            'Pengguna memberi akses penuh untuk menjalankan tugas ini.',
            'Setiap kali mulai bekerja, langkah pertama membaca AGENTS.md di workspace sebelum tindakan lain.',
            'Boleh menambah todo Trello berdasarkan temuan atau kebutuhan MVP, dengan checklist spesifik dan tanpa duplikat.',
            'Ikuti seluruh aturan AGENTS.md, validasi perubahan sebelum selesai, dan jangan push tanpa syarat yang diminta.',
        ]
        if self.status_provider is not None:
            try:
                lines.extend(['', 'Konteks status terbaru:', self.status_provider.summary()])
            except Exception as error:
                lines.extend(['', f'Konteks status gagal dimuat: {error}'])
        lines.extend(['', 'Pertanyaan pengguna:', question])
        return os.linesep.join(lines)

    @staticmethod
    def _limited(text: str, limit: int = 3800) -> str:
        if len(text) <= limit:
            return text
        return text[:limit].rstrip() + os.linesep + '... Jawaban dipotong.'
