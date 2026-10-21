from __future__ import annotations

import re
import secrets


def generate_wifi_password(length: int = 10) -> str:
    alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def make_username(payment_id: str) -> str:
    safe_id = re.sub(r'[^a-zA-Z0-9_-]+', '-', payment_id).strip('-').lower()
    return f'wifi-{safe_id}'
