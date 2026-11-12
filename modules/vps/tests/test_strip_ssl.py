import unittest

from modules.vps.templates import NGINX_CI_MONITOR, NGINX_DEFAULT, NGINX_SITES, strip_ssl


class StripSslTest(unittest.TestCase):
    def test_tidak_menyisakan_direktif_ssl(self):
        for name, content in NGINX_SITES.items():
            result = strip_ssl(content)
            self.assertNotIn('ssl_certificate', result, name)
            self.assertNotIn('ssl_certificate_key', result, name)
            self.assertNotIn('ssl_dhparam', result, name)
            self.assertNotIn('letsencrypt/options-ssl', result, name)

    def test_tidak_menyisakan_listen_443(self):
        for name, content in NGINX_SITES.items():
            result = strip_ssl(content)
            for line in result.splitlines():
                if line.strip().startswith('listen'):
                    self.assertNotIn('443', line, name)

    def test_brace_tetap_seimbang(self):
        for name, content in NGINX_SITES.items():
            result = strip_ssl(content)
            self.assertEqual(result.count('{'), result.count('}'), name)

    def test_ci_monitor_listen_selalu_di_dalam_blok(self):
        result = strip_ssl(NGINX_CI_MONITOR)
        depth = 0
        for line in result.splitlines():
            stripped = line.strip()
            if stripped.startswith('listen'):
                self.assertEqual(depth, 1, 'listen di luar blok: %r' % line)
            depth += stripped.count('{') - stripped.count('}')
        self.assertEqual(depth, 0)

    def test_redirect_ke_https_dibuang(self):
        result = strip_ssl(NGINX_SITES['be-haidi20'])
        self.assertNotIn('return 301 https', result)

    def test_default_tetap_layani_port_80_dan_proxy_api(self):
        result = strip_ssl(NGINX_DEFAULT)
        self.assertIn('listen 80 default_server;', result)
        self.assertIn('proxy_pass http://127.0.0.1:3000', result)


if __name__ == '__main__':
    unittest.main()
