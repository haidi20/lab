import os
from dataclasses import dataclass


@dataclass
class VPSConfig:
    host: str = '172.232.126.138'
    port: int = 22
    user: str = 'root'
    password: str = ''
    key_path: str = ''
    deploy_root: str = '/var/www/hello'
    repo_dir: str = '/var/www/hello-repo'
    repo_url: str = 'https://github.com/haidi20/haidi20.git'
    domain: str = 'haidinata.my.id'
    be_port: int = 3000

    @classmethod
    def from_env(cls) -> 'VPSConfig':
        return cls(
            host=os.environ.get('VPS_HOST', cls.host),
            port=int(os.environ.get('VPS_PORT', cls.port)),
            user=os.environ.get('VPS_USER', cls.user),
            password=os.environ.get('VPS_PASSWORD', ''),
            key_path=os.environ.get('VPS_SSH_KEY', ''),
            deploy_root=os.environ.get('VPS_DEPLOY_ROOT', cls.deploy_root),
        )
