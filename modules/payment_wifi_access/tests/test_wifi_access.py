import unittest

from modules.payment_wifi_access import (
    MockWifiAccessAdapter,
    PaymentConfirmation,
    RouterOSRestAdapter,
    WifiAccessService,
)


def payment(payment_id: str = 'PAY-001') -> PaymentConfirmation:
    return PaymentConfirmation(payment_id=payment_id, invoice_id='INV-001', duration_hours=24)


class WifiAccessServiceTest(unittest.TestCase):
    def test_paid_payment_creates_unique_24h_access(self) -> None:
        adapter = MockWifiAccessAdapter()
        service = WifiAccessService(adapter, {'PAY-001': 'INV-001'})

        result = service.grant_access_after_payment(payment())

        self.assertEqual(result.username, 'wifi-pay-001')
        self.assertEqual(result.adapter, 'mock')

    def test_each_payment_has_different_password(self) -> None:
        adapter = MockWifiAccessAdapter()
        paid = {'PAY-001': 'INV-001', 'PAY-002': 'INV-002'}
        service = WifiAccessService(adapter, paid)

        first = service.grant_access_after_payment(payment('PAY-001'))
        second = service.grant_access_after_payment(PaymentConfirmation('PAY-002', 'INV-002'))

        self.assertNotEqual(first.password, second.password)
        self.assertNotEqual(first.username, second.username)

    def test_payment_cannot_be_reused(self) -> None:
        service = WifiAccessService(MockWifiAccessAdapter(), {'PAY-001': 'INV-001'})
        service.grant_access_after_payment(payment())

        with self.assertRaises(ValueError):
            service.grant_access_after_payment(payment())

    def test_unpaid_payment_is_rejected(self) -> None:
        service = WifiAccessService(MockWifiAccessAdapter(), set())

        with self.assertRaises(PermissionError):
            service.grant_access_after_payment(payment())

    def test_routeros_scheduler_uses_valid_policy(self) -> None:
        adapter = RouterOSRestAdapter('192.0.2.1', 'admin', 'secret')
        requests = []

        def fake_request(method, path, payload=None):
            requests.append((method, path, payload))
            if path == '/system/clock':
                return {'date': '2026-10-20', 'time': '10:00:00'}
            return {}

        adapter._request = fake_request
        adapter.activate(payment())

        scheduler_payload = requests[-1][2]
        self.assertEqual(scheduler_payload['policy'], 'read,write,test')


if __name__ == '__main__':
    unittest.main()
