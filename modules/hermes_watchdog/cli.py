from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from modules.hermes_watchdog.notifier import TelegramNotifier
from modules.hermes_watchdog.service import HermesWatchdog


_HIDE_FLAGS = getattr(subprocess, 'CREATE_NO_WINDOW', 0) if os.name == 'nt' else 0

def resolve_command(command: list[str]) -> list[str]:
    if not command:
        return command
    executable = shutil.which(command[0])
    return [executable or command[0], *command[1:]]


def load_env_file(path: str | Path) -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        os.environ[key.strip()] = value.strip().strip(chr(39)).strip(chr(34))


def build_watchdog_from_env(env_path: str | Path = '.env') -> HermesWatchdog:
    load_env_file(env_path)
    hermes_home = Path(os.environ.get('HERMES_HOME', str(Path.home() / 'AppData' / 'Local' / 'hermes')))
    workdir = Path(os.environ.get('KLINIK_WORKDIR', 'D:/projects/klinik-git'))
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.environ.get('HERMES_WATCHDOG_TELEGRAM_CHAT_ID', '')
    notifier = None
    if token and chat_id.isdigit():
        notifier = TelegramNotifier(token, int(chat_id))

    def read_cron() -> dict[str, object]:
        path = hermes_home / 'cron' / 'jobs.json'
        try:
            payload = json.loads(path.read_text(encoding='utf-8'))
            return payload if isinstance(payload, dict) else {'jobs': []}
        except (OSError, ValueError):
            return {'jobs': []}

    def read_git_status() -> str:
        try:
            completed = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=str(workdir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                creationflags=_HIDE_FLAGS,
                timeout=15,
            )
        except (OSError, subprocess.SubprocessError):
            return ''
        if completed.returncode != 0:
            return ''
        return completed.stdout.decode('utf-8', errors='replace')

    def run_command(command: list[str], timeout: float) -> object:
        return subprocess.run(
            resolve_command(command),
            cwd=str(workdir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            creationflags=_HIDE_FLAGS,
            timeout=timeout,
        )

    return HermesWatchdog(
        cron_reader=read_cron,
        log_path=hermes_home / 'logs' / 'agent.log',
        git_status_reader=read_git_status,
        command_runner=run_command,
        notifier=notifier,
        state_path=hermes_home / 'watchdog' / 'state.json',
        stale_minutes=float(os.environ.get('HERMES_WATCHDOG_STALE_MINUTES', '15')),
        job_id=os.environ.get('HERMES_WATCHDOG_JOB_ID', '442bba7081d8'),
        hermes_binary=os.environ.get('HERMES_BIN', 'hermes'),
        command_timeout=float(os.environ.get('HERMES_WATCHDOG_COMMAND_TIMEOUT_SECONDS', '120')),
        prune_interval_minutes=float(os.environ.get('HERMES_WATCHDOG_PRUNE_INTERVAL_MINUTES', '360')),
        prune_older_than=os.environ.get('HERMES_WATCHDOG_PRUNE_OLDER_THAN', '1d'),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--interval', type=float, default=300.0)
    parser.add_argument('--env', default='.env')
    arguments = parser.parse_args()
    watchdog = build_watchdog_from_env(arguments.env)

    while True:
        try:
            result = watchdog.check()
            stamp = time.strftime('%Y-%m-%d %H:%M:%S')
            print(f'{stamp} status={result.status} action={result.action} {result.detail}', flush=True)
        except Exception as error:
            print(f'watchdog error: {error}', flush=True)
        if arguments.once:
            return
        time.sleep(max(30.0, arguments.interval))
