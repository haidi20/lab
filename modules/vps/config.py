import os
from dataclasses import dataclass


@dataclass
class VPSConfig:
    host: str = '172.232.112.39'
    port: int = 22
    user: str = 'root'
    password: str = ''
    key_path: str = ''
    deploy_root: str = '/var/www/hello'
    repo_dir: str = '/var/www/hello-repo'
    repo_url: str = 'https://github.com/haidi20/haidi20.git'
    karta_repo_dir: str = '/var/www/karta'
    karta_repo_url: str = 'https://github.com/utamaweb/karta_spa.git'
    klinik_repo_dir: str = '/var/www/klinik'
    klinik_repo_url: str = 'https://github.com/haidi20/klinik.git'
    domain: str = 'haidinata.my.id'
    be_port: int = 3000

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
        )


def load_env(path):
    key = 'VPS_'
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())
