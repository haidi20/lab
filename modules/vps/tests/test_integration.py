import unittest
import os

from modules.vps.config import VPSConfig, load_env

load_env(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))

from modules.vps.ssh import SSHRunner


RUN_INTEGRATION = os.environ.get('VPS_HOST', '') not in ('', '123.45.67.89')


@unittest.skipUnless(RUN_INTEGRATION, 'VPS_HOST not set to real VPS')
class IntegrationSSHTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config = VPSConfig.from_env()
        cls.runner = SSHRunner(config)

    @classmethod
    def tearDownClass(cls):
        cls.runner.close()

    def _run(self, command):
        stdout, stderr, code = self.runner.run(command)
        self.assertEqual(code, 0, 'command failed: %s\n%s' % (command, stderr))
        return stdout

    def test_01_nginx_config_valid(self):
        out = self._run('nginx -t 2>&1')
        self.assertIn('syntax is ok', out)

    def test_02_services_active(self):
        for svc in ('nginx', 'php8.3-fpm', 'redis-server'):
            out = self._run('systemctl is-active %s' % svc)
            self.assertEqual(out.strip(), 'active', 'service %s not active' % svc)

    def test_03_certbot_certs_cover_all_subdomains(self):
        out = self._run('certbot certificates 2>/dev/null')
        self.assertIn('Certificate Name', out, 'certbot has no certs at all')

    def test_04_repo_dirs_exist(self):
        out = self._run('ls /var/www/')
        for d in ('haidi', 'karta', 'skripsi'):
            self.assertIn(d, out)

    def test_05_all_subdomains_respond_200(self):
        for sub in ('haidinata.my.id', 'be.haidinata.my.id', 'ci.haidinata.my.id',
                    'karta.haidinata.my.id', 'inventory.haidinata.my.id'):
            code = self._run(
                'curl -skL -o /dev/null -w "%%{http_code}" https://%s' % sub
            ).strip()
            self.assertEqual(code, '200', '%s returned %s' % (sub, code))


if __name__ == '__main__':
    unittest.main()
