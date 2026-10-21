import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from modules.payment_wifi_access import render_login_page, render_mikrotik_login_page
from modules.payment_wifi_access.build import write_mikrotik_login_page


class HotspotPortalPagesTest(unittest.TestCase):
    def test_login_page_posts_credentials_to_router(self) -> None:
        html = render_login_page(
            login_url='https://192.168.1.10/login',
            next_url='https://example.com/success',
        )

        self.assertIn('action="https://192.168.1.10/login"', html)
        self.assertIn('name="username"', html)
        self.assertIn('name="password"', html)
        self.assertIn('name="dst"', html)
        self.assertIn('value="https://example.com/success"', html)
        self.assertIn('name="popup"', html)

    def test_login_page_shows_error_when_provided(self) -> None:
        html = render_login_page(
            login_url='https://192.168.1.10/login',
            next_url='https://example.com/success',
            error_message='Username atau password salah',
        )

        self.assertIn('Username atau password salah', html)

    def test_login_page_uses_clean_soft_sky_theme(self) -> None:
        html = render_login_page(
            login_url='https://192.168.1.10/login',
            next_url='https://example.com/success',
        )

        self.assertIn('class="page"', html)
        self.assertIn('class="card"', html)
        self.assertIn('--sky-50', html)
        self.assertIn('--sky-600', html)
        self.assertIn('linear-gradient', html)

    def test_login_page_has_accessible_password_toggle(self) -> None:
        html = render_login_page(
            login_url='https://192.168.1.10/login',
            next_url='https://example.com/success',
        )

        self.assertIn('id="password-toggle"', html)
        self.assertIn('aria-controls="password"', html)
        self.assertIn('aria-label="Tampilkan password"', html)
        self.assertIn('data-visible-label="Sembunyikan"', html)

    def test_login_page_supports_brand_and_support_message(self) -> None:
        html = render_login_page(
            login_url='https://192.168.1.10/login',
            next_url='https://example.com/success',
            brand_name='Kantor Cabang A',
            support_message='Butuh bantuan? Hubungi kasir.',
        )

        self.assertIn('Kantor Cabang A', html)
        self.assertIn('Butuh bantuan? Hubungi kasir.', html)

    def test_mikrotik_login_page_uses_router_variables(self) -> None:
        html = render_mikrotik_login_page(brand_name='WiFi Kafe')

        self.assertIn('action="$(link-login-only)"', html)
        self.assertIn('name="username"', html)
        self.assertIn('name="password"', html)
        self.assertIn('value="$(link-orig)"', html)
        self.assertIn('$(if error)', html)
        self.assertIn('$(error)', html)
        self.assertIn('$(endif)', html)
        self.assertIn('WiFi Kafe', html)

    def test_write_mikrotik_login_page_creates_file(self) -> None:
        with TemporaryDirectory() as directory:
            output = Path(directory) / 'login.html'

            write_mikrotik_login_page(output, brand_name='WiFi Kafe')

            html = output.read_text(encoding='utf-8')
            self.assertIn('action="$(link-login-only)"', html)
            self.assertIn('WiFi Kafe', html)
