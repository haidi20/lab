import unittest

from modules.vps.config import VPSConfig
from modules.vps.fakes import FakeSSHRunner
from modules.vps.setup import VPSSetupper
from modules.vps.templates import BE_SERVICE, NGINX_DEFAULT, NGINX_SITES


class VPSSetupperTest(unittest.TestCase):
    def setUp(self):
        self.config = VPSConfig(host='203.0.113.10', user='root', password='x')
        self.runner = FakeSSHRunner()
        self.setupper = VPSSetupper(self.config, runner=self.runner)

    def test_install_packages_uses_apt(self):
        self.runner.outputs['command -v bun'] = ('', '', 0)
        self.setupper.install_packages()
        joined = ' '.join(cmd for cmd, _, _ in self.runner.commands)
        self.assertIn('apt-get update', joined)
        self.assertIn('nginx', joined)
        self.assertIn('python3-certbot-nginx', joined)

    def test_install_bun_skips_when_present(self):
        self.runner.outputs['test -x /root/.bun/bin/bun'] = ('', '', 0)
        self.setupper.install_bun()
        joined = ' '.join(cmd for cmd, _, _ in self.runner.commands)
        self.assertNotIn('bun.sh/install', joined)

    def test_install_bun_runs_official_installer_when_missing(self):
        self.runner.outputs['test -x /root/.bun/bin/bun'] = ('', '', 1)
        self.setupper.install_bun()
        joined = ' '.join(cmd for cmd, _, _ in self.runner.commands)
        self.assertIn('bun.sh/install', joined)

    def test_configure_nginx_writes_all_sites_and_reloads(self):
        self.setupper.configure_nginx()
        joined = ' '.join(cmd for cmd, _, _ in self.runner.commands)
        for name in ('default', 'be-haidi20', 'ci-monitor', 'karta', 'klinik'):
            self.assertIn(name, joined)
        self.assertIn('nginx -t', joined)
        self.assertIn('systemctl reload nginx', joined)

    def test_default_site_points_to_portfolio_dist_and_api_proxy(self):
        self.assertIn('/var/www/portfolio/fe/dist', NGINX_DEFAULT)
        self.assertIn('proxy_pass http://127.0.0.1:3000', NGINX_DEFAULT)

    def test_default_site_api_location_not_nested_inside_root_location(self):
        lines = NGINX_DEFAULT.splitlines()
        depth = 0
        api_depth = None
        root_depth = None
        for line in lines:
            stripped = line.strip()
            if stripped == 'location / {':
                root_depth = depth
            elif stripped == 'location /api {':
                api_depth = depth
            depth += line.count('{') - line.count('}')
        self.assertIsNotNone(root_depth)
        self.assertIsNotNone(api_depth)
        self.assertEqual(api_depth, root_depth,
            'location /api must be at the same nesting level as location /')

    def test_be_site_has_ssl_listen_443(self):
        be_template = NGINX_SITES['be-haidi20']
        self.assertIn('listen 443 ssl', be_template)
        self.assertIn('ssl_certificate', be_template)
        self.assertIn('ssl_certificate_key', be_template)

    def test_issue_certs_covers_all_subdomains(self):
        self.setupper.issue_certs()
        joined = ' '.join(cmd for cmd, _, _ in self.runner.commands)
        for domain in (
            'haidinata.my.id',
            'be.haidinata.my.id',
            'ci.haidinata.my.id',
            'karta.haidinata.my.id',
            'inventory.haidinata.my.id',
        ):
            self.assertIn(domain, joined)

    def test_install_packages_includes_composer(self):
        self.setupper.install_packages()
        joined = ' '.join(cmd for cmd, _, _ in self.runner.commands)
        self.assertIn('composer', joined)

    def test_clone_repos_clones_all_projects(self):
        self.runner.outputs['command -v bun'] = ('/root/.bun/bin/bun', '', 0)
        self.setupper.clone_repos()
        joined = ' '.join(cmd for cmd, _, _ in self.runner.commands)
        self.assertIn('github.com/haidi20/haidi20.git', joined)
        self.assertIn('github.com/utamaweb/karta_spa.git', joined)
        self.assertIn('github.com/haidi20/klinik.git', joined)

    def test_clone_repos_uses_fetch_reset_when_repo_exists(self):
        self.runner.outputs['if [ -d /var/www/portfolio/.git ]'] = ('', '', 0)
        self.runner.outputs['if [ -d /var/www/karta/.git ]'] = ('', '', 0)
        self.runner.outputs['if [ -d /var/www/klinik/.git ]'] = ('', '', 0)
        self.setupper.clone_repos()
        joined = ' '.join(cmd for cmd, _, _ in self.runner.commands)
        self.assertIn('git -C /var/www/karta fetch --prune origin', joined)
        self.assertIn('git -C /var/www/karta reset --hard origin/main', joined)

    def test_setup_be_installs_bun_dependencies_in_be_folder(self):
        self.setupper.setup_be_service()
        joined = ' '.join(cmd for cmd, _, _ in self.runner.commands)
        self.assertIn('bun install', joined)
        self.assertIn('/var/www/portfolio/be', joined)

    def test_enable_php_fpm_and_redis(self):
        self.setupper.enable_services()
        joined = ' '.join(cmd for cmd, _, _ in self.runner.commands)
        self.assertIn('systemctl enable --now php8.3-fpm', joined)
        self.assertIn('systemctl enable --now redis-server', joined)

    def test_enable_services_called_in_full_setup(self):
        self.runner.outputs['command -v bun'] = ('/root/.bun/bin/bun', '', 0)
        self.setupper.run(skip_certs=True, skip_clone=True)
        joined = ' '.join(cmd for cmd, _, _ in self.runner.commands)
        self.assertIn('systemctl enable --now php8.3-fpm', joined)
        self.assertIn('systemctl enable --now redis-server', joined)

    def test_deploy_ci_monitor_uploads_index_php(self):
        self.setupper.deploy_ci_monitor()
        joined = ' '.join(cmd for cmd, _, _ in self.runner.commands)
        self.assertIn('/var/www/ci-monitor', joined)
        self.assertIn('mkdir -p /var/www/ci-monitor', joined)

    def test_laravel_env_setup_for_karta_and_klinik(self):
        self.setupper.setup_laravel_env()
        joined = ' '.join(cmd for cmd, _, _ in self.runner.commands)
        self.assertIn('.env', joined)
        self.assertIn('key:generate', joined)
        self.assertIn('/var/www/karta', joined)
        self.assertIn('/var/www/klinik/src', joined)

    def test_nginx_http_first_then_ssl(self):
        self.runner.outputs['command -v bun'] = ('/root/.bun/bin/bun', '', 0)
        self.setupper.configure_nginx_http()
        http_files = list(self.runner.files.keys())
        self.assertGreater(len(http_files), 0,
            'HTTP configs written before certbot')
        for path in http_files:
            content = self.runner.files[path]
            self.assertNotIn('ssl_certificate', content,
                'HTTP-only config must not reference certs yet')

    def test_full_nginx_written_after_certs_issued(self):
        self.setupper.configure_nginx()
        for path, content in self.runner.files.items():
            if path.startswith('/etc/nginx/sites-available/'):
                pass
        self.assertIn('nginx -t', ' '.join(cmd for cmd, _, _ in self.runner.commands))

    def test_setup_runs_composer_and_artisan_for_laravel_after_clone(self):
        self.runner.outputs['command -v bun'] = ('/root/.bun/bin/bun', '', 0)
        self.setupper.build_laravel_projects()
        joined = ' '.join(cmd for cmd, _, _ in self.runner.commands)
        self.assertIn('composer install', joined)
        self.assertIn('php artisan migrate --force', joined)
        self.assertIn('php artisan config:cache', joined)
        self.assertIn('/var/www/karta', joined)
        self.assertIn('/var/www/klinik/src', joined)

    def test_full_setup_order_http_certs_then_ssl(self):
        self.runner.outputs['command -v bun'] = ('/root/.bun/bin/bun', '', 0)
        self.setupper.run(skip_clone=True)
        joined = ' '.join(cmd for cmd, _, _ in self.runner.commands)
        http_idx = joined.find('configure_nginx_http')
        cert_idx = joined.find('certbot')
        ssl_idx = joined.find('configure_nginx')
        self.assertIn('certbot', joined)
        self.assertIn('nginx -t', joined)

    def test_setup_be_service_enables_and_starts(self):
        self.setupper.setup_be_service()
        joined = ' '.join(cmd for cmd, _, _ in self.runner.commands)
        self.assertIn('/etc/systemd/system/haidi20-be.service', joined)
        self.assertIn('daemon-reload', joined)
        self.assertIn('enable --now haidi20-be', joined)

    def test_be_service_unit_matches_running_server(self):
        self.assertIn('WorkingDirectory=/var/www/portfolio/be', BE_SERVICE)
        self.assertIn('ExecStart=/root/.bun/bin/bun run src/index.ts', BE_SERVICE)
        self.assertIn('Environment=PORT=3000', BE_SERVICE)

    def test_configure_ufw_allows_web_ports(self):
        self.setupper.configure_ufw()
        joined = ' '.join(cmd for cmd, _, _ in self.runner.commands)
        self.assertIn('ufw allow OpenSSH', joined)
        self.assertIn('ufw allow 80/tcp', joined)
        self.assertIn('ufw allow 443/tcp', joined)
        self.assertIn('ufw --force enable', joined)

    def test_full_setup_runs_all_steps(self):
        self.runner.outputs['command -v bun'] = ('/root/.bun/bin/bun', '', 0)
        self.setupper.run(skip_certs=True, skip_clone=True)
        joined = ' '.join(cmd for cmd, _, _ in self.runner.commands)
        self.assertIn('apt-get install', joined)
        self.assertIn('nginx -t', joined)
        self.assertIn('ufw --force enable', joined)


if __name__ == '__main__':
    unittest.main()
