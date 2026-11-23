"""Helper SSH sementara untuk setup VPS.

Kredensial wajib dari environment: `VPS_HOST`, `VPS_USER`, `VPS_PASSWORD`
(lihat `.env`). Tidak ada default password di source.

Pemakaian:
  python vps_run.py "command"            # jalankan command, tunggu sampai selesai
  python vps_run.py --bg "command"       # jalankan command di background (nohup)
  python vps_run.py --log                # tampilkan tail /root/setup.log
"""
import os
import sys

import paramiko

from modules.vps.config import load_env

load_env('.env')
HOST = os.environ.get('VPS_HOST', '')

USER = os.environ.get('VPS_USER', '')


def password():
    value = os.environ.get('VPS_PASSWORD', '')
    if not value:
        raise RuntimeError('VPS_PASSWORD wajib diisi di .env (tidak ada default)')
    return value


def connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, int(os.environ.get('VPS_PORT', '22')), USER, password=password(), timeout=30)
    return client


def main():
    args = sys.argv[1:]
    client = connect()
    try:
        if args and args[0] == '--log':
            n = args[1] if len(args) > 1 else '60'
            _, out, _ = client.exec_command('tail -n %s /root/setup.log' % n)
            sys.stdout.write(out.read().decode())
            return
        if args and args[0] == '--bg':
            cmd = args[1]
            _, out, err = client.exec_command(
                "nohup bash -c %r > /root/setup.log 2>&1 & echo LAUNCHED" % cmd
            )
        else:
            cmd = args[0] if args else 'echo ok'
            _, out, err = client.exec_command(cmd, timeout=300)
        code = out.channel.recv_exit_status()
        sys.stdout.write(out.read().decode())
        err_text = err.read().decode()
        if err_text:
            sys.stderr.write(err_text)
        sys.exit(code)
    finally:
        client.close()


if __name__ == '__main__':
    main()
