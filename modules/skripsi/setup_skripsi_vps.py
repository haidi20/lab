#!/usr/bin/env python3
"""Setup skripsi.haidinata.my.id (monitoring-ph-air) di VPS baru via SSH.

Langkah:
1. Bootstrap clone repo GitHub ke /var/www/monitoring-ph-air.
2. Jalankan deploy/setup-vps.sh (paket, MySQL, composer/npm build,
   import SQL, migrate, nginx).
3. Jalankan deploy/setup-ssl.sh (certbot HTTPS).
4. Verifikasi https://skripsi.haidinata.my.id

Pakai:
    python modules/skripsi/setup_skripsi_vps.py            # full setup
    python modules/skripsi/setup_skripsi_vps.py --check    # verifikasi saja
"""
import argparse
import os
import sys

import paramiko

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PASSWORD_ENV = "VPS_PASSWORD"
DOMAIN = "skripsi.haidinata.my.id"
APP_DIR = "/var/www/monitoring-ph-air"
REPO_URL = "https://github.com/haidi20/monitoring-ph-air.git"


def load_env():
    path = os.path.join(PROJECT_ROOT, ".env")
    if not os.path.isfile(path):
        return
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


def host():
    return os.environ.get("VPS_HOST", "172.232.96.174")


def user():
    return os.environ.get("VPS_USER", "root")


def log(msg):
    print("[skripsi-setup] %s" % msg, flush=True)


def password():
    value = os.environ.get(PASSWORD_ENV, "")
    if not value:
        raise RuntimeError("VPS_PASSWORD wajib diisi di .env (tidak ada default)")
    return value


def connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host(), username=user(), password=password(), timeout=30)
    return client


def run(client, command, timeout=1800):
    """Jalankan command di VPS, tampilkan output live, return exit code."""
    log("RUN: %s" % command[:120])
    stdin, stdout, stderr = client.exec_command(command, timeout=timeout, get_pty=True)
    while True:
        if stdout.channel.exit_status_ready():
            break
        while stdout.channel.recv_ready():
            sys.stdout.write(stdout.channel.recv(4096).decode(errors="replace"))
            sys.stdout.flush()
    while stdout.channel.recv_ready():
        sys.stdout.write(stdout.channel.recv(4096).decode(errors="replace"))
    sys.stdout.flush()
    return stdout.channel.recv_exit_status()


def bootstrap_clone(client):
    """Clone atau reset repo di VPS agar deploy/ script tersedia."""
    log("1/4 bootstrap clone repo di VPS ...")
    cmd = (
        "if [ -d {d}/.git ]; then git -C {d} fetch origin && "
        "git -C {d} reset --hard origin/main; "
        "else git clone {r} {d}; fi"
    ).format(d=APP_DIR, r=REPO_URL)
    code = run(client, cmd, timeout=600)
    if code != 0:
        raise RuntimeError("bootstrap clone gagal (code %d)" % code)


def run_app_setup(client):
    log("2/4 jalankan deploy/setup-vps.sh (paket, mysql, build, db, nginx) ...")
    code = run(
        client,
        "cd %s && APP_URL=%s FORCE_IMPORT_SQL=true bash deploy/setup-vps.sh" % (APP_DIR, DOMAIN),
        timeout=3600,
    )
    if code != 0:
        raise RuntimeError("setup-vps.sh re-run gagal (code %d)" % code)


def run_ssl_setup(client):
    log("3/4 jalankan deploy/setup-ssl.sh (certbot HTTPS) ...")
    code = run(
        client,
        "cd %s && APP_URL=%s bash deploy/setup-ssl.sh" % (APP_DIR, DOMAIN),
        timeout=900,
    )
    if code != 0:
        raise RuntimeError("setup-ssl.sh gagal (code %d)" % code)


def verify_public(client):
    log("4/4 verifikasi HTTP/HTTPS ...")
    run(client, "systemctl is-active nginx mysql php8.3-fpm redis-server || true")
    run(client, "curl -sS -o /dev/null -w 'http  %%{http_code}\\n' --max-time 30 http://%s/" % DOMAIN)
    code = run(client, "curl -sS -o /dev/null -w 'https %%{http_code}\\n' --max-time 30 https://%s/" % DOMAIN)
    return code


def main():
    load_env()
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verifikasi saja, tanpa setup")
    args = parser.parse_args()

    log("target: https://%s (VPS %s)" % (DOMAIN, host()))
    client = connect()
    try:
        if not args.check:
            bootstrap_clone(client)
            run_app_setup(client)
            run_ssl_setup(client)
        code = verify_public(client)
        log("selesai. cek manual: https://%s/" % DOMAIN)
        return 0
    except RuntimeError as error:
        log("ERROR: %s" % error)
        return 1
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
