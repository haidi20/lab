from __future__ import annotations

import json
import urllib.request
from typing import Callable


Poster = Callable[[str, dict[str, object]], dict[str, object]]


class TelegramNotifier:
    def __init__(
        self,
        token: str,
        chat_id: int,
        poster: Poster | None = None,
        timeout: float = 30.0,
    ) -> None:
        if not token:
            raise ValueError('Telegram bot token is required')
        if chat_id <= 0:
            raise ValueError('Telegram chat id is required')
        self.token = token
        self.chat_id = chat_id
        self.timeout = timeout
        self.poster = poster or self._http_post

    def send(self, text: str) -> None:
        url = f'https://api.telegram.org/bot{self.token}/sendMessage'
        payload = {
            'chat_id': self.chat_id,
            'text': text,
            'disable_web_page_preview': True,
        }
        self.poster(url, payload)

    @staticmethod
    def _http_post(url: str, payload: dict[str, object]) -> dict[str, object]:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
