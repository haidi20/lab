from __future__ import annotations

import base64
import json
import os
import ssl
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from typing import Protocol

from modules.payment_wifi_access.models import ActivationResult, PaymentConfirmation
from modules.payment_wifi_access.password import generate_wifi_password, make_username


class WifiAccessAdapter(Protocol):
    def activate(self, payment: PaymentConfirmation) -> ActivationResult:
        ...


class MockWifiAccessAdapter:
    def __init__(self) -> None:
        self.activations: dict[str, ActivationResult] = {}

    def activate(self, payment: PaymentConfirmation) -> ActivationResult:
        username = make_username(payment.payment_id)
        password = f'wifi-{generate_wifi_password()}'
        result = ActivationResult(
            username=username,
            password=password,
            expires_at=int(time.time()) + payment.duration_hours * 3600,
            adapter='mock',
        )
        self.activations[payment.payment_id] = result
        return result


class RouterOSRestAdapter:
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        *,
        hotspot_profile: str = 'default',
        verify_tls: bool = True,
        auto_expire_on_router: bool = True,
    ) -> None:
        self.base_url = 'https://' + host.rstrip('/') + '/rest'
        self.username = username
        self.password = password
        self.hotspot_profile = hotspot_profile
        self.verify_tls = verify_tls
        self.auto_expire_on_router = auto_expire_on_router

    def activate(self, payment: PaymentConfirmation) -> ActivationResult:
        username = make_username(payment.payment_id)
        password = f'wifi-{generate_wifi_password()}'
        expires_at = int(time.time()) + payment.duration_hours * 3600
        payload = {
            'name': username,
            'password': password,
            'profile': self.hotspot_profile,
            'comment': f'payment_id={payment.payment_id};invoice={payment.invoice_id};expires_at={expires_at}',
            'limit-uptime': f'{payment.duration_hours}h',
        }
        self._request('POST', '/ip/hotspot/user', payload)

        if self.auto_expire_on_router:
            self._schedule_removal(username, payment.duration_hours)

        return ActivationResult(username, password, expires_at, adapter='routeros-rest')

    def _schedule_removal(self, username: str, duration_hours: int) -> None:
        clock = self._request('GET', '/system/clock')
        router_now = datetime.fromisoformat(f'{clock["date"]}T{clock["time"]}')
        router_expires = router_now + timedelta(hours=duration_hours)
        scheduler_name = f'remove-{username}'
        script = (
            f'/ip hotspot active remove [find user="{username}"]; '
            f'/ip hotspot user remove [find name="{username}"]; '
            f'/system scheduler remove [find name="{scheduler_name}"]'
        )
        payload = {
            'name': scheduler_name,
            'start-date': router_expires.strftime('%Y-%m-%d'),
            'start-time': router_expires.strftime('%H:%M:%S'),
            'interval': '0s',
            'on-event': script,
            'policy': 'read,write,test',
        }
        self._request('POST', '/system/scheduler', payload)

    def _request(self, method: str, path: str, payload: dict[str, str] | None = None) -> dict[str, object]:
        body = None if payload is None else json.dumps(payload).encode()
        auth = base64.b64encode(f'{self.username}:{self.password}'.encode()).decode()
        headers = {'Content-Type': 'application/json', 'Authorization': f'Basic {auth}'}
        context = None
        if not self.verify_tls:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        request = urllib.request.Request(self.base_url + path, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, context=context, timeout=10) as response:
                raw = response.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as error:
            detail = error.read().decode(errors='replace')
            raise RuntimeError(f'RouterOS API error {error.code}: {detail}') from error
