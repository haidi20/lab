import os
from dataclasses import dataclass

DEFAULT_REPO_DIRS = ("monitoring-ph-air",)


@dataclass
class VPSConfig:
    host: str = '172.232.96.174'
    port: int = 22
    user: str = 'root'
    password: str = ''
    key_path: str = ''
    deploy_root: str = '/var/www/portfolio/fe/dist'
    repo_dir: str = '/var/www/portfolio'
    repo_url: str = 'https://github.com/haidi20/haidi20.git'
    karta_repo_dir: str = '/var/www/karta'
    karta_repo_url: str = 'https://github.com/utamaweb/karta_spa.git'
    klinik_repo_dir: str = '/var/www/klinik'
    klinik_repo_url: str = 'https://github.com/haidi20/klinik.git'
    domain: str = 'haidinata.my.id'
    be_port: int = 3000
    lab_repo_dir: str = '/var/www/ci-monitor-repo'
    lab_repo_url: str = 'https://github.com/haidi20/lab.git'
    ci_monitor_root: str = '/var/www/ci-monitor-repo/modules/vps/ci_monitor'
    portfolio_branch: str = 'main'
    karta_branch: str = 'main'
    klinik_branch: str = 'haidi'
    karta_db: str = 'karta'
    klinik_db: str = 'klinik'
    github_token: str = ''

    @classmethod
    def from_env(cls, env_file=None):
        if env_file is None:
            default_env = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                '.env'
            )
            if os.path.isfile(default_env):
                env_file = default_env
        if env_file:
            load_env(env_file)
        return cls(
            host=os.environ.get('VPS_HOST', cls.host),
            port=int(os.environ.get('VPS_PORT', cls.port)),
            user=os.environ.get('VPS_USER', cls.user),
            password=os.environ.get('VPS_PASSWORD', ''),
            key_path=os.environ.get('VPS_SSH_KEY', ''),
            deploy_root=os.environ.get('VPS_DEPLOY_ROOT', cls.deploy_root),
            github_token=os.environ.get('GITHUB_TOKEN', ''),
        )


def load_env(path):
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())


def expected_repo_dirs():
    """Daftar direktori repo di /var/www yang diharapkan ada.

    Default mengikuti VPS haidinata saat ini (`monitoring-ph-air`); bisa
    dioverride lewat `VPS_EXPECTED_REPO_DIRS` (dipisah koma).
    """
    raw = os.environ.get('VPS_EXPECTED_REPO_DIRS', '')
    items = [item.strip() for item in raw.split(',') if item.strip()]
    return items or list(DEFAULT_REPO_DIRS)
