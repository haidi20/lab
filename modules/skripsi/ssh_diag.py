#!/usr/bin/env python3
"""Helper: jalankan satu command di VPS skripsi. Usage: python ssh_diag.py "command" """
import os
import sys

import paramiko


def password():
    value = os.environ.get("VPS_PASSWORD", "")
    if not value:
        raise RuntimeError("VPS_PASSWORD wajib diisi di .env (tidak ada default)")
    return value


def main(argv):
    host = os.environ.get("VPS_HOST", "172.232.96.174")
    user = os.environ.get("VPS_USER", "root")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=user, password=password(), timeout=30)
    try:
        command = argv[1] if len(argv) > 1 else "echo ok"
        stdin, stdout, stderr = client.exec_command(command, timeout=120)
        out = stdout.read().decode(errors="replace")
        err = stderr.read().decode(errors="replace")
        print(out)
        if err.strip():
            print("[stderr]", err)
    finally:
        client.close()


if __name__ == "__main__":
    main(sys.argv)