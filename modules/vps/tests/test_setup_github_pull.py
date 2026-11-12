import unittest

from modules.vps.config import VPSConfig
from modules.vps.fakes import FakeSSHRunner
from modules.vps.setup import VPSSetupper


def make_setupper(token='ghp_test'):
    config = VPSConfig(host='1.2.3.4', password='x', github_token=token)
    runner = FakeSSHRunner()
    return VPSSetupper(config, runner=runner), runner


def commands(runner):
    return [c[0] for c in runner.commands if not c[0].startswith('write:')]


class GitCredentialsTest(unittest.TestCase):
    def test_menulis_credential_store_dan_mode_600(self):
        setup, runner = make_setupper('ghp_abc123')
        setup.ensure_git_credentials()
        content = runner.files['/root/.git-credentials']
        self.assertIn('ghp_abc123', content)
        self.assertIn('https://x-access-token:ghp_abc123@github.com', content)
        self.assertIn(('write:/root/.git-credentials', 0, '600'), runner.commands)
        self.assertIn('git config --global credential.helper store', commands(runner))

    def test_tanpa_token_tidak_menulis_apa_pun(self):
        setup, runner = make_setupper('')
        setup.ensure_git_credentials()
        self.assertNotIn('/root/.git-credentials', runner.files)

    def test_menulis_token_ci_monitor_ke_etc_environment(self):
        setup, runner = make_setupper('ghp_abc123')
        setup.ensure_git_credentials()
        content = runner.files['/etc/environment']
        self.assertIn('KARTA_GIT_TOKEN=ghp_abc123', content)
        self.assertIn(('write:/etc/environment', 0, '644'), runner.commands)


class CloneReposTest(unittest.TestCase):
    def test_clone_empat_repo_dengan_branch_masing_masing(self):
        setup, runner = make_setupper()
        setup.clone_repos()
        cmds = '\n'.join(commands(runner))
        for url in (
            'https://github.com/haidi20/haidi20.git',
            'https://github.com/utamaweb/karta_spa.git',
            'https://github.com/haidi20/klinik.git',
            'https://github.com/haidi20/lab.git',
        ):
            self.assertIn(url, cmds, 'repo %s tidak di-clone' % url)
        self.assertIn('origin/main', cmds)
        self.assertIn('origin/haidi', cmds)

    def test_idempoten_pakai_fetch_reset_bukan_clone_ulang(self):
        setup, runner = make_setupper()
        setup.clone_repos()
        cmds = '\n'.join(commands(runner))
        self.assertIn('if [ -d', cmds)
        self.assertIn('git -C', cmds)
        self.assertIn('reset --hard', cmds)


class CiMonitorTest(unittest.TestCase):
    def test_root_nginx_dari_repo_bukan_file_lokal(self):
        setup, runner = make_setupper()
        setup.deploy_ci_monitor()
        self.assertNotIn('/var/www/ci-monitor/index.php', runner.files)
        cmds = '\n'.join(commands(runner))
        self.assertIn('/var/www/ci-monitor-repo', cmds)


class LaravelProjectsTest(unittest.TestCase):
    def test_karta_dibuat_db_env_dan_build(self):
        setup, runner = make_setupper()
        runner.outputs['cat /var/www/karta/.env'] = ('', '', 1)
        setup.prepare_laravel_projects()
        cmds = '\n'.join(commands(runner))
        self.assertIn('CREATE DATABASE IF NOT EXISTS', cmds)
        self.assertIn('CREATE USER IF NOT EXISTS', cmds)
        self.assertIn('composer install --no-dev', cmds)
        self.assertIn('npm ci', cmds)
        self.assertIn('npm run prod', cmds)
        self.assertIn('php artisan migrate --force', cmds)

    def test_klinik_build_dan_migrate_serta_env_production(self):
        setup, runner = make_setupper()
        setup.prepare_laravel_projects()
        cmds = '\n'.join(commands(runner))
        self.assertIn('/var/www/klinik/src', cmds)
        env = runner.files.get('/var/www/klinik/src/.env', '')
        self.assertIn('APP_ENV=production', env)
        self.assertIn('APP_DEBUG=false', env)
        self.assertIn('DB_PORT=3306', env)
        self.assertIn('FILESYSTEM_DISK=local', env)
        self.assertIn('QUEUE_CONNECTION=redis', env)

    def test_env_tidak_ditimpa_bila_sudah_ada_dan_password_dipakai_ulang(self):
        setup, runner = make_setupper()
        runner.outputs['cat /var/www/karta/.env'] = (
            'DB_PASSWORD=rahasia123\nAPP_KEY=base64:abc\n', '', 0)
        setup.prepare_laravel_projects()
        env = runner.files.get('/var/www/karta/.env', '')
        self.assertIn('DB_PASSWORD=rahasia123', env)
        self.assertIn('APP_KEY=base64:abc', env)
        self.assertIn('APP_ENV=production', env)

    def test_permission_storage_www_data(self):
        setup, runner = make_setupper()
        setup.prepare_laravel_projects()
        cmds = '\n'.join(commands(runner))
        self.assertIn('chown -R www-data:www-data', cmds)

    def test_supervisor_klinik_dipasang_dari_repo(self):
        setup, runner = make_setupper()
        setup.configure_supervisor()
        cmds = '\n'.join(commands(runner))
        self.assertIn('/var/www/klinik/deploy/supervisor/', cmds)
        self.assertIn('supervisorctl update', cmds)


class RunOrderTest(unittest.TestCase):
    def test_run_memanggil_prepare_laravel_dan_build(self):
        setup, runner = make_setupper()
        calls = []
        for name in ('install_packages', 'install_bun', 'ensure_git_credentials',
                     'clone_repos', 'build_and_deploy_portfolio',
                     'prepare_laravel_projects', 'deploy_ci_monitor',
                     'configure_nginx_http', 'enable_services', 'setup_be_service',
                     'configure_supervisor', 'configure_ufw', 'configure_nginx'):
            setattr(setup, name, lambda n=name: calls.append(n))
        setup.run(skip_certs=True)
        self.assertEqual(calls, [
            'install_packages', 'install_bun', 'ensure_git_credentials',
            'clone_repos', 'build_and_deploy_portfolio', 'prepare_laravel_projects',
            'deploy_ci_monitor', 'configure_nginx_http', 'enable_services',
            'setup_be_service', 'configure_supervisor', 'configure_ufw',
            'configure_nginx',
        ])

    def test_skip_clone_melewati_clone_dan_build(self):
        setup, runner = make_setupper()
        calls = []
        for name in ('install_packages', 'install_bun', 'ensure_git_credentials',
                     'clone_repos', 'build_and_deploy_portfolio',
                     'prepare_laravel_projects', 'deploy_ci_monitor',
                     'configure_nginx_http', 'enable_services', 'setup_be_service',
                     'configure_supervisor', 'configure_ufw', 'configure_nginx'):
            setattr(setup, name, lambda n=name: calls.append(n))
        setup.run(skip_certs=True, skip_clone=True)
        self.assertNotIn('clone_repos', calls)
        self.assertNotIn('prepare_laravel_projects', calls)
        self.assertIn('configure_nginx', calls)


if __name__ == '__main__':
    unittest.main()
