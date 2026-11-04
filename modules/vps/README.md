# modules/vps

Provisioning & deployment toolkit untuk replika VPS haidinata.my.id
(Ubuntu 24.04, nginx, Bun + Hono BE, PHP-FPM, Certbot, UFW).

## CLI

    python -m modules.vps audit    # snapshot kondisi VPS
    python -m modules.vps setup    # bootstrap penuh: packages, bun, repo, nginx, systemd, ufw, certbot
    python -m modules.vps setup --skip-certs --skip-clone
    python -m modules.vps deploy --local-dist D:/learns/haidi20/dist
    python -m modules.vps health   # cek nginx, haidi20-be, HTTP 200

Kredensial dibaca dari .env: VPS_HOST, VPS_PORT, VPS_USER,
VPS_PASSWORD, VPS_SSH_KEY, VPS_DEPLOY_ROOT.

## Struktur

- config.py - dataclass VPSConfig + loader .env
- ssh.py - SSHRunner (paramiko): run, read/write file, upload tree
- templates.py - nginx sites & systemd unit, sama persis dengan server berjalan
- setup.py - VPSSetupper, langkah idempoten
- audit.py / health.py - snapshot & health check
- deploy.py - upload folder dist + reload nginx
- tests/ - unit test dengan FakeSSHRunner (tanpa jaringan)

## Test

    python -m unittest modules.vps.tests.test_vps_setup modules.vps.tests.test_vps_tools
