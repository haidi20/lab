import unittest

from modules.vps.templates import NGINX_BE, NGINX_SITES


class BeTemplateTest(unittest.TestCase):
    def test_root_be_mengarah_ke_health(self):
        self.assertIn('location = /', NGINX_BE)
        self.assertIn('proxy_pass http://127.0.0.1:3000/api/health;', NGINX_BE)

    def test_semua_site_wajib_ada(self):
        for name in ('default', 'be-haidi20', 'ci-monitor', 'karta', 'klinik'):
            self.assertIn(name, NGINX_SITES)

    def test_ci_monitor_root_dari_repo(self):
        self.assertIn('/var/www/ci-monitor-repo/modules/vps/ci_monitor', NGINX_SITES['ci-monitor'])

    def test_default_melayani_domain_utama(self):
        self.assertIn('server_name haidinata.my.id www.haidinata.my.id _;', NGINX_SITES['default'])


if __name__ == '__main__':
    unittest.main()
