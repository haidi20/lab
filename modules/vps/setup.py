from modules.vps.templates import (
    BE_SERVICE,
    CICD_LARAVEL,
    CICD_PORTFOLIO,
    NGINX_SITES,
)

APT_PACKAGES = (
    'nginx certbot python3-certbot-nginx supervisor ufw git curl '
    'php8.3-fpm redis-server'
)

BUN_INSTALL_CMD = (
    'curl -fsSL https://bun.sh/install | bash'
)


class VPSSetupper:
    """Idempotent bootstrap replicating the current haidinata.my.id VPS."""

    def __init__(self, config, runner=None):
        self.config = config
        self.runner = runner

    def _run(self, command, timeout=600):
        stdout, stderr, code = self.runner.run(command, timeout=timeout)
        if code != 0:
            raise RuntimeError('command failed (%s): %s' % (code, command))
        return stdout

    def install_packages(self):
        self._run('apt-get update -y', timeout=900)
        self._run('DEBIAN_FRONTEND=noninteractive apt-get install -y %s' % APT_PACKAGES, timeout=1800)

    def install_bun(self):
        _, _, code = self.runner.run('command -v bun')
        if code != 0:
            self._run(BUN_INSTALL_CMD, timeout=600)

    def clone_repo(self):
        self._run(
            'if [ -d %s/.git ]; then cd %s && git pull; else git clone %s %s; fi'
            % (self.config.repo_dir, self.config.repo_dir, self.config.repo_url, self.config.repo_dir)
        )

    def build_and_deploy_portfolio(self):
        self._run('cd %s/fe && bun install && bun run build' % self.config.repo_dir, timeout=1200)
        self._run('rm -rf %s && mkdir -p %s' % (self.config.deploy_root, self.config.deploy_root))
        self._run('cp -r %s/fe/dist/. %s/' % (self.config.repo_dir, self.config.deploy_root))

    def configure_nginx(self):
        for name, content in NGINX_SITES.items():
            self.runner.write_file('/etc/nginx/sites-available/%s' % name, content)
            self._run('ln -sf /etc/nginx/sites-available/%s /etc/nginx/sites-enabled/%s' % (name, name))
        self._run('nginx -t')
        self._run('systemctl reload nginx')

    def setup_be_service(self):
        self.runner.write_file('/etc/systemd/system/haidi20-be.service', BE_SERVICE, mode='644')
        self._run('systemctl daemon-reload')
        self._run('systemctl enable --now haidi20-be')

    def issue_certs(self):
        self._run(
            'certbot -n --nginx -d %s -d www.%s --agree-tos --register-unsafely-without-email'
            % (self.config.domain, self.config.domain),
            timeout=600,
        )
        for subdomain in ('be', 'ci', 'karta', 'inventory'):
            fqdn = '%s.%s' % (subdomain, self.config.domain)
            self._run(
                'certbot -n --nginx -d %s --agree-tos --register-unsafely-without-email'
                % fqdn,
                timeout=600,
            )

    def configure_ufw(self):
        self._run('ufw allow OpenSSH')
        self._run('ufw allow 80/tcp')
        self._run('ufw allow 443/tcp')
        self._run('ufw --force enable')

    def configure_cicd(self):
        portfolio_wf = '/var/www/hello-repo/.github/workflows/deploy.yml'
        self.runner.write_file(portfolio_wf, CICD_PORTFOLIO)
        karta_wf = '%s/.github/workflows/deploy.yml' % self.config.karta_repo_dir
        self.runner.write_file(
            karta_wf,
            CICD_LARAVEL.format(name='karta', branch='main', repo_dir=self.config.karta_repo_dir),
        )
        klinik_wf = '%s/.github/workflows/deploy.yml' % self.config.klinik_repo_dir
        self.runner.write_file(
            klinik_wf,
            CICD_LARAVEL.format(name='klinik', branch='haidi', repo_dir=self.config.klinik_repo_dir),
        )

    def run(self, skip_certs=False, skip_clone=False):
        self.install_packages()
        self.install_bun()
        if not skip_clone:
            self.clone_repo()
            self.build_and_deploy_portfolio()
        self.configure_nginx()
        self.setup_be_service()
        self.configure_ufw()
        self.configure_cicd()
        if not skip_certs:
            self.issue_certs()
