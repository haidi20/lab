import os
from pathlib import Path

from modules.payment_wifi_access import MockWifiAccessAdapter, PaymentConfirmation, RouterOSRestAdapter, WifiAccessService


def load_env_file(path: Path = Path('.env')) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
4

def main() -> None:
    load_env_file()

    paid_payments = {'PAY-001': 'INV-001'}
    payment = PaymentConfirmation(
        payment_id='PAY-001',
        invoice_id='INV-001',
        customer_name='Andi',
        duration_hours=24,
    )

    mock_adapter = MockWifiAccessAdapter()
    access = WifiAccessService(mock_adapter, paid_payments).grant_access_after_payment(payment)
    print('Mode mock:', access)

    host = os.environ.get('MIKROTIK_HOST')
    if host:
        real_adapter = RouterOSRestAdapter(
            host=host,
            username=os.environ.get('MIKROTIK_USER', ''),
            password=os.environ.get('MIKROTIK_PASSWORD', ''),
            hotspot_profile=os.environ.get('MIKROTIK_HOTSPOT_PROFILE', 'default'),
            verify_tls=os.environ.get('MIKROTIK_VERIFY_TLS', 'true').lower() != 'false',
            auto_expire_on_router=os.environ.get('MIKROTIK_AUTO_EXPIRE', 'true').lower() != 'false',
        )
        real_access = WifiAccessService(real_adapter, paid_payments).grant_access_after_payment(payment)
        print('Mode RouterOS:', real_access)
    else:
        print('MIKROTIK_HOST belum diset, jadi kode hanya menjalankan simulator/mock.')


if __name__ == '__main__':
    main()
