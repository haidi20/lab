import unittest

from modules.vps.audit import collect_audit
from modules.vps.deploy import deploy_all_sites, deploy_dist, deploy_site
from modules.vps.fakes import FakeSSHRunner
from modules.vps.health import check_health


class AuditTest(unittest.TestCase):
    def test_collect_audit_returns_sections(self):
        runner = FakeSSHRunner()
        runner.outputs['ls /var/www'] = ('hello\nkarta\n', '', 0)
        result = collect_audit(runner)
        self.assertIn('os', result)
        self.assertIn('nginx_files', result)
        self.assertEqual(result['www'], ['hello', 'karta'])


class HealthTest(unittest.TestCase):
    def test_check_health_returns_status_map(self):
        runner = FakeSSHRunner()
        runner.outputs['systemctl is-active nginx'] = ('active', '', 0)
        result = check_health(runner)
        self.assertEqual(result['nginx']['output'], 'active')
        self.assertIn('be_http', result)


class DeployTest(unittest.TestCase):
    def test_deploy_uploads_and_reloads_nginx(self):
        runner = FakeSSHRunner()
        count = deploy_dist(runner, 'local/dist', '/var/www/hello')
        self.assertIn(('local/dist', '/var/www/hello'), runner.uploaded)
        joined = ' '.join(cmd for cmd, _, _ in runner.commands)
        self.assertIn('systemctl reload nginx', joined)
        self.assertEqual(count, 0)

    def test_deploy_site_uploads_and_reloads_nginx(self):
        runner = FakeSSHRunner()
        count = deploy_site(runner, 'local/karta/public', '/var/www/karta/public')
        self.assertIn(('local/karta/public', '/var/www/karta/public'), runner.uploaded)
        joined = ' '.join(cmd for cmd, _, _ in runner.commands)
        self.assertIn('systemctl reload nginx', joined)
        self.assertEqual(count, 0)

    def test_deploy_all_sites_uploads_to_each_root(self):
        runner = FakeSSHRunner()
        results = deploy_all_sites(
            runner,
            {
                'portfolio': 'local/dist',
                'karta': 'local/karta/public',
                'klinik': 'local/klinik/src/public',
            },
        )
        self.assertIn(('local/dist', '/var/www/hello'), runner.uploaded)
        self.assertIn(('local/karta/public', '/var/www/karta/public'), runner.uploaded)
        self.assertIn(('local/klinik/src/public', '/var/www/klinik/src/public'), runner.uploaded)
        self.assertEqual(len(results), 3)


if __name__ == '__main__':
    unittest.main()
