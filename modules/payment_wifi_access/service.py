from __future__ import annotations

from modules.payment_wifi_access.adapters import WifiAccessAdapter
from modules.payment_wifi_access.models import ActivationResult, PaymentConfirmation


class WifiAccessService:
    def __init__(self, adapter: WifiAccessAdapter, paid_payments: dict[str, str]) -> None:
        self.adapter = adapter
        self.paid_payments = paid_payments
        self.activated_payment_ids: set[str] = set()

    def grant_access_after_payment(self, payment: PaymentConfirmation) -> ActivationResult:
        if payment.payment_id not in self.paid_payments:
            raise PermissionError(f'Payment {payment.payment_id} has not been paid')
        if self.paid_payments[payment.payment_id] != payment.invoice_id:
            raise ValueError('Payment does not match the invoice')
        if payment.payment_id in self.activated_payment_ids:
            raise ValueError(f'Payment {payment.payment_id} was already used')
        if payment.duration_hours <= 0:
            raise ValueError('Duration must be greater than zero')

        result = self.adapter.activate(payment)
        self.activated_payment_ids.add(payment.payment_id)
        return result
