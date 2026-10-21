from __future__ import annotations

import argparse
from pathlib import Path

from modules.payment_wifi_access.pages import render_mikrotik_login_page


def write_mikrotik_login_page(
    output_path: Path,
    brand_name: str = 'WiFi Access',
    support_message: str | None = None,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_mikrotik_login_page(brand_name=brand_name, support_message=support_message),
        encoding='utf-8',
    )
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description='Generate a RouterOS Hotspot login page.')
    parser.add_argument('--output', type=Path, default=Path('public/login.html'))
    parser.add_argument('--brand', default='WiFi Access')
    parser.add_argument('--support-message')
    args = parser.parse_args()

    output = write_mikrotik_login_page(args.output, args.brand, args.support_message)
    print(f'Login page generated: {output}')


if __name__ == '__main__':
    main()
