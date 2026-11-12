import os
import secrets

from modules.vps.templates import (
    BE_SERVICE,
    CICD_LARAVEL,
    CICD_PORTFOLIO,
    NGINX_SITES,
    strip_ssl,
)

APT_PACKAGES = (
    'nginx certbot python3-certbot-nginx supervisor ufw git curl unzip '
    'php8.3-fpm php8.3-cli php8.3-mbstring php8.3-xml php8.3-curl php8.3-zip '
    'php8.3-mysql php8.3-intl php8.3-bcmath php8.3-gd php8.3-redis '
    'php8.3-opcache redis-server composer'
)

BUN_INSTALL_CMD = 'curl -fsSL https://bun.sh/install | bash'
BUN = '/root/.bun/bin/bun'

GIT_CREDENTIALS = '/root/.git-credentials'
SYSTEM_ENVIRONMENT = '/etc/environment'


class VPSSetupper:
    """Idempotent bootstrap for haidinata.my.id; semua deploy pull dari GitHub."""

    def __init__(self, config, runner=None):
        self.config = config
        self.runner = runner

    def _run(self, command, timeout=600):
        stdout, stderr, code = self.runner.run(command, timeout=timeout)
        if code != 0:
            raise RuntimeError('command failed (%s): %s\n%s' % (code, command, stderr))
        return stdout

    def _try(self, command, timeout=600):
        return self.runner.run(command, timeout=timeout)[2]

    def install_packages(self):
        self._run('apt-get update -y', timeout=900)
        self._run(
            'DEBIAN_FRONTEND=noninteractive apt-get install -y %s' % APT_PACKAGES,
            timeout=1800,
        )

    def install_bun(self):
        if self._try('test -x %s' % BUN) != 0:
            self._run(BUN_INSTALL_CMD, timeout=600)

    def ensure_git_credentials(self):
        token = self.config.github_token
        if not token:
            return
        self.runner.write_file(
            GIT_CREDENTIALS,
            'https://x-access-token:%s@github.com\n' % token,
            mode='600',
        )
        self._run('git config --global credential.helper store')
        current = self.runner.read_file(SYSTEM_ENVIRONMENT) or ''
        lines = [line for line in current.splitlines()
                 if not line.startswith('KARTA_GIT_TOKEN=')]
        lines.append('KARTA_GIT_TOKEN=%s' % token)
        self.runner.write_file(SYSTEM_ENVIRONMENT, '\n'.join(lines) + '\n', mode='644')

    def _sync_repo(self, repo_dir, repo_url, branch):
        self._run(
            'if [ -d {d}/.git ]; then '
            'git -C {d} fetch --prune origin && git -C {d} reset --hard origin/{b}; '
            'else git clone --branch {b} {u} {d}; fi'.format(
                d=repo_dir, b=branch, u=repo_url),
            timeout=900,
        )

    def clone_repos(self):
        for repo_dir, repo_url, branch in (
            (self.config.repo_dir, self.config.repo_url, self.config.portfolio_branch),
            (self.config.karta_repo_dir, self.config.karta_repo_url, self.config.karta_branch),
            (self.config.klinik_repo_dir, self.config.klinik_repo_url, self.config.klinik_branch),
            (self.config.lab_repo_dir, self.config.lab_repo_url, self.config.portfolio_branch),
        ):
            self._sync_repo(repo_dir, repo_url, branch)

    def clone_repo(self):
        self.clone_repos()

    def build_and_deploy_portfolio(self):
        self._run('cd %s/fe && %s install && %s run build' % (self.config.repo_dir, BUN, BUN), timeout=1200)
        self._run('rm -rf %s && mkdir -p %s' % (self.config.deploy_root, self.config.deploy_root))
        self._run('cp -r %s/fe/dist/. %s/' % (self.config.repo_dir, self.config.deploy_root))

    def deploy_ci_monitor(self):
        self._run('mkdir -p %s' % self.config.ci_monitor_root)
        self._run('test -f %s/index.php' % self.config.ci_monitor_root)

    def configure_nginx(self):
        for name, content in NGINX_SITES.items():
            self.runner.write_file('/etc/nginx/sites-available/%s' % name, content)
            self._run('ln -sf /etc/nginx/sites-available/%s /etc/nginx/sites-enabled/%s' % (name, name))
        self._run('nginx -t')
        self._run('systemctl reload nginx')

    def configure_nginx_http(self):
        for name, content in NGINX_SITES.items():
            http_content = strip_ssl(content)
            self.runner.write_file('/etc/nginx/sites-available/%s' % name, http_content)
            self._run('ln -sf /etc/nginx/sites-available/%s /etc/nginx/sites-enabled/%s' % (name, name))
        self._run('nginx -t')
        self._run('systemctl reload nginx')

    @staticmethod
    def _set_env(text, key, value):
        lines = text.splitlines()
        prefix = key + '='
        for index, line in enumerate(lines):
            if line.startswith(prefix):
                lines[index] = prefix + value
                break
        else:
            lines.append(prefix + value)
        return '\n'.join(lines) + '\n'

    @staticmethod
    def _read_env(text, key):
        for line in text.splitlines():
            if line.startswith(key + '='):
                return line.split('=', 1)[1].strip()
        return ''

    def _ensure_database(self, db_name, db_user, db_password):
        escaped = db_password.replace("'", "''")
        statements = [
            "CREATE DATABASE IF NOT EXISTS `%s` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" % db_name,
        ]
        for host in ('localhost', '127.0.0.1'):
            statements.append(
                "CREATE USER IF NOT EXISTS '%s'@'%s' IDENTIFIED BY '%s';"
                % (db_user, host, escaped))
            statements.append(
                "ALTER USER '%s'@'%s' IDENTIFIED BY '%s';" % (db_user, host, escaped))
            statements.append(
                "GRANT ALL PRIVILEGES ON `%s`.* TO '%s'@'%s';" % (db_name, db_user, host))
        statements.append('FLUSH PRIVILEGES;')
        sql = ' '.join(statements).replace("'", "'\\''")
        self._run("mysql -e '%s'" % sql)

    def _prepare_laravel_app(self, repo_dir, db_name, db_user, app_url,
                             build_command, extra_env):
        existing = self.runner.read_file('%s/.env' % repo_dir) or ''
        db_password = self._read_env(existing, 'DB_PASSWORD')
        if not db_password:
            db_password = secrets.token_urlsafe(18).replace('-', '').replace('_', '')
        self._ensure_database(db_name, db_user, db_password)

        complete = any(line.startswith('APP_KEY=') for line in existing.splitlines()) and \
            'DB_DATABASE=' in existing
        if complete:
            base = existing
        else:
            base = self.runner.read_file('%s/.env.example' % repo_dir) or existing
        app_key = self._read_env(base, 'APP_KEY')
        base = self._set_env(base, 'APP_ENV', 'production')
        base = self._set_env(base, 'APP_DEBUG', 'false')
        base = self._set_env(base, 'APP_URL', app_url)
        base = self._set_env(base, 'DB_CONNECTION', 'mysql')
        base = self._set_env(base, 'DB_HOST', '127.0.0.1')
        base = self._set_env(base, 'DB_PORT', '3306')
        base = self._set_env(base, 'DB_DATABASE', db_name)
        base = self._set_env(base, 'DB_USERNAME', db_user)
        base = self._set_env(base, 'DB_PASSWORD', db_password)
        for key, value in extra_env.items():
            base = self._set_env(base, key, value)
        if not app_key:
            base = self._set_env(base, 'APP_KEY', '')
        self.runner.write_file('%s/.env' % repo_dir, base, mode='640')

        self._run('cd %s && mkdir -p storage/framework/cache/data '
                  'storage/framework/views storage/framework/sessions storage/logs '
                  'bootstrap/cache' % repo_dir)
        self._run('cd %s && COMPOSER_ALLOW_SUPERUSER=1 composer install --no-dev '
                  '--optimize-autoloader --no-interaction' % repo_dir, timeout=1800)
        if not app_key:
            self._run('cd %s && php artisan key:generate --force' % repo_dir)
        if build_command:
            self._run('cd %s && %s' % (repo_dir, build_command), timeout=1800)
        self._run('cd %s && php artisan migrate --force' % repo_dir, timeout=900)
        self._try('cd %s && php artisan storage:link' % repo_dir)
        self._run('chown -R www-data:www-data %s/storage %s/bootstrap/cache' % (repo_dir, repo_dir))
        self._run('cd %s && php artisan config:cache' % repo_dir)
        self._try('cd %s && php artisan route:cache' % repo_dir)

    @staticmethod
    def _reuse_or_random(existing, key, generator):
        value = VPSSetupper._read_env(existing, key)
        if value and value.lower() not in ('null', '""'):
            return value
        return generator()

    def prepare_karta(self):
        self._prepare_laravel_app(
            self.config.karta_repo_dir,
            self.config.karta_db,
            'karta',
            'https://karta.%s' % self.config.domain,
            'npm ci --no-audit --no-fund && NODE_OPTIONS=--openssl-legacy-provider npm run prod',
            {'CACHE_DRIVER': 'file', 'SESSION_DRIVER': 'file', 'QUEUE_CONNECTION': 'sync'},
        )

    def prepare_laravel_projects(self):
        self.prepare_karta()
        self.prepare_klinik()

    def prepare_klinik(self):
        klinik_dir = '%s/src' % self.config.klinik_repo_dir
        existing = self.runner.read_file('%s/.env' % klinik_dir) or ''
        reverb_env = {
            'CACHE_STORE': 'redis',
            'SESSION_DRIVER': 'redis',
            'QUEUE_CONNECTION': 'redis',
            'REDIS_CLIENT': 'predis',
            'REDIS_HOST': '127.0.0.1',
            'REDIS_PASSWORD': 'null',
            'REDIS_PORT': '6379',
            'FILESYSTEM_DISK': 'local',
            'TENANT_FILESYSTEM_DRIVER': 'local',
            'TENANCY_SUFFIX_STORAGE_PATH': 'true',
            'BROADCAST_CONNECTION': 'reverb',
            'REVERB_HOST': 'inventory.%s' % self.config.domain,
            'REVERB_PORT': '443',
            'REVERB_SCHEME': 'https',
            'VITE_REVERB_HOST': 'inventory.%s' % self.config.domain,
            'VITE_REVERB_PORT': '443',
            'VITE_REVERB_SCHEME': 'https',
            'REVERB_APP_ID': self._reuse_or_random(
                existing, 'REVERB_APP_ID',
                lambda: str(secrets.randbelow(900000) + 100000)),
            'REVERB_APP_KEY': self._reuse_or_random(
                existing, 'REVERB_APP_KEY', lambda: secrets.token_hex(10)),
            'REVERB_APP_SECRET': self._reuse_or_random(
                existing, 'REVERB_APP_SECRET', lambda: secrets.token_hex(16)),
            'JWT_SECRET': self._reuse_or_random(
                existing, 'JWT_SECRET', lambda: secrets.token_hex(32)),
        }
        reverb_env['VITE_REVERB_APP_KEY'] = reverb_env['REVERB_APP_KEY']
        self._prepare_laravel_app(
            klinik_dir,
            self.config.klinik_db,
            'klinik',
            'https://inventory.%s' % self.config.domain,
            'npm ci --no-audit --no-fund && npm run build',
            reverb_env,
        )

    def build_laravel_projects(self):
        self.prepare_laravel_projects()

    def configure_supervisor(self):
        supervisor_dir = '%s/deploy/supervisor' % self.config.klinik_repo_dir
        self._run('cp %s/*.conf /etc/supervisor/conf.d/' % supervisor_dir)
        self._run('systemctl restart supervisor')
        self._try('supervisorctl reread')
        self._try('supervisorctl update')
        self._try(
            "(crontab -u www-data -l 2>/dev/null; "
            "echo '* * * * * cd %s/src && php artisan schedule:run >> /dev/null 2>&1') "
            "| crontab -u www-data -" % self.config.klinik_repo_dir
        )

    def setup_be_service(self):
        self._run('cd %s/be && %s install' % (self.config.repo_dir, BUN), timeout=600)
        self.runner.write_file('/etc/systemd/system/haidi20-be.service', BE_SERVICE, mode='644')
        self._run('systemctl daemon-reload')
        self._run('systemctl enable --now haidi20-be')
        self._run('systemctl restart haidi20-be')

    def enable_services(self):
        self._run('systemctl enable --now php8.3-fpm')
        self._run('systemctl enable --now redis-server')
        self._run('systemctl enable --now supervisor')

    def setup_laravel_env(self):
        self.prepare_laravel_projects()

    def issue_certs(self):
        self._run(
            'certbot -n --nginx -d %s -d www.%s --agree-tos '
            '--register-unsafely-without-email --redirect' % (
                self.config.domain, self.config.domain),
            timeout=600,
        )
        for subdomain in ('be', 'ci', 'karta', 'inventory'):
            fqdn = '%s.%s' % (subdomain, self.config.domain)
            self._run(
                'certbot -n --nginx -d %s --agree-tos '
                '--register-unsafely-without-email --redirect' % fqdn,
                timeout=600,
            )

    def configure_ufw(self):
        self._try('ufw allow OpenSSH')
        self._try('ufw allow 80/tcp')
        self._try('ufw allow 443/tcp')
        self._try('ufw --force enable')

    def _ensure_workflow(self, repo_dir, content):
        path = '%s/.github/workflows/deploy.yml' % repo_dir
        if self.runner.read_file(path).strip():
            return
        self.runner.write_file(path, content)

    def configure_cicd(self):
        self._ensure_workflow(self.config.repo_dir, CICD_PORTFOLIO)
        self._ensure_workflow(
            self.config.karta_repo_dir,
            CICD_LARAVEL.format(name='karta', branch=self.config.karta_branch,
                                repo_dir=self.config.karta_repo_dir),
        )
        self._ensure_workflow(
            self.config.klinik_repo_dir,
            CICD_LARAVEL.format(name='klinik', branch=self.config.klinik_branch,
                                repo_dir=self.config.klinik_repo_dir),
        )

    def run(self, skip_certs=False, skip_clone=False):
        self.install_packages()
        self.install_bun()
        self.ensure_git_credentials()
        if not skip_clone:
            self.clone_repos()
            self.build_and_deploy_portfolio()
            self.prepare_laravel_projects()
            self.deploy_ci_monitor()
        self.configure_nginx_http()
        self.enable_services()
        self.setup_be_service()
        self.configure_supervisor()
        self.configure_ufw()
        self.configure_cicd()
        if not skip_certs:
            self.issue_certs()
        self.configure_nginx()
