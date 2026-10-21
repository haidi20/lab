from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PaymentConfirmation:
    payment_id: str
    invoice_id: str
    customer_name: str = ''
    duration_hours: int = 24
    mac_address: str | None = None


@dataclass(frozen=True)
class ActivationResult:
    username: str
    password: str
    expires_at: int
    adapter: str
