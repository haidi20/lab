import unittest
import os
import tempfile

from modules.vps.audit import collect_audit
from modules.vps.config import VPSConfig, load_env
from modules.vps.deploy import deploy_all_sites, deploy_dist, deploy_from_git, deploy_site
from modules.vps.fakes import FakeSSHRunner
from modules.vps.health import check_health


class AuditTest(unittest.TestCase):
    def test_collect_audit_returns_sections(self):
        runner = FakeSSHRunner()
        runner.outputs['ls /var/www'] = ('portfolio\nkarta\n', '', 0)
        result = collect_audit(runner)
        self.assertIn('os', result)
        self.assertIn('nginx_files', result)
        self.assertEqual(result['www'], ['portfolio', 'karta'])


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
        count = deploy_dist(runner, 'local/dist', '/var/www/portfolio/fe/dist')
        self.assertIn(('local/dist', '/var/www/portfolio/fe/dist'), runner.uploaded)
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
        config = VPSConfig()
        deploy_all_sites(runner, config, ['portfolio', 'karta', 'klinik'])
        joined = ' '.join(cmd for cmd, _, _ in runner.commands)
        self.assertEqual(joined.count('git pull'), 3)
        self.assertIn('bun run build', joined)
        self.assertIn('composer install', joined)

    def test_deploy_from_git_pulls_and_builds_on_vps(self):
        runner = FakeSSHRunner()
        config = VPSConfig()
        deploy_from_git(runner, config, 'portfolio')
        joined = ' '.join(cmd for cmd, _, _ in runner.commands)
        self.assertIn('git pull', joined)
        self.assertIn('bun install', joined)
        self.assertIn('bun run build', joined)
        self.assertIn('/var/www/portfolio', joined)
        self.assertIn('systemctl reload nginx', joined)

    def test_deploy_from_git_karta_uses_composer_and_laravel_root(self):
        runner = FakeSSHRunner()
        config = VPSConfig()
        deploy_from_git(runner, config, 'karta')
        joined = ' '.join(cmd for cmd, _, _ in runner.commands)
        self.assertIn('git pull', joined)
        self.assertIn('composer install', joined)
        self.assertIn('php artisan', joined)
        self.assertIn('/var/www/karta', joined)

    def test_deploy_from_git_klinik_uses_composer_and_laravel_root(self):
        runner = FakeSSHRunner()
        config = VPSConfig()
        deploy_from_git(runner, config, 'klinik')
        joined = ' '.join(cmd for cmd, _, _ in runner.commands)
        self.assertIn('git pull', joined)
        self.assertIn('composer install', joined)
        self.assertIn('php artisan', joined)
        self.assertIn('/var/www/klinik/src', joined,
            'klinik Laravel app is inside src/ subdirectory')

    def test_deploy_portfolio_always_uses_git_pull_not_local_upload(self):
        runner = FakeSSHRunner()
        config = VPSConfig()
        deploy_from_git(runner, config, 'portfolio')
        upload_calls = [u for u in runner.uploaded]
        joined = ' '.join(cmd for cmd, _, _ in runner.commands)
        self.assertIn('git pull', joined)
        self.assertEqual(upload_calls, [],
            'portfolio deploy must not upload from local; it pulls from git on VPS')

    def test_setup_installs_cicd_workflows_for_all_projects(self):
        from modules.vps.setup import VPSSetupper
        config = VPSConfig()
        runner = FakeSSHRunner()
        setupper = VPSSetupper(config, runner=runner)
        setupper.configure_cicd()
        written_files = list(runner.files.keys())
        for repo_dir in ('/var/www/portfolio', '/var/www/karta', '/var/www/klinik'):
            wf_path = '%s/.github/workflows/deploy.yml' % repo_dir
            self.assertIn(wf_path, written_files)
            self.assertIn('git pull', runner.files[wf_path])


if __name__ == '__main__':
    unittest.main()




class LoadEnvTest(unittest.TestCase):
    def test_load_env_reads_file_and_sets_environ(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write('VPS_HOST=172.232.112.39\nVPS_PORT=22\n')
            path = f.name
        try:
            os.environ.pop('VPS_HOST', None)
            os.environ.pop('VPS_PORT', None)
            load_env(path)
            self.assertEqual(os.environ['VPS_HOST'], '172.232.112.39')
            self.assertEqual(os.environ['VPS_PORT'], '22')
        finally:
            os.unlink(path)
            os.environ.pop('VPS_HOST', None)
            os.environ.pop('VPS_PORT', None)

    def test_load_env_does_not_overwrite_existing(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write('VPS_HOST=1.2.3.4\n')
            path = f.name
        try:
            os.environ['VPS_HOST'] = '9.9.9.9'
            load_env(path)
            self.assertEqual(os.environ['VPS_HOST'], '9.9.9.9')
        finally:
            os.unlink(path)
            os.environ.pop('VPS_HOST', None)

    def test_from_env_reads_dotenv(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write('VPS_HOST=10.0.0.1\nVPS_PORT=2222\n')
            path = f.name
        try:
            os.environ.pop('VPS_HOST', None)
            os.environ.pop('VPS_PORT', None)
            config = VPSConfig.from_env(env_file=path)
            self.assertEqual(config.host, '10.0.0.1')
            self.assertEqual(config.port, 2222)
        finally:
            os.unlink(path)
            os.environ.pop('VPS_HOST', None)
            os.environ.pop('VPS_PORT', None)


if __name__ == '__main__':
    unittest.main()
