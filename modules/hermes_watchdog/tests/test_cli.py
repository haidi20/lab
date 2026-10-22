from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from modules.hermes_watchdog import cli as watchdog_cli
from modules.hermes_watchdog.cli import build_watchdog_from_env
from modules.hermes_watchdog.notifier import TelegramNotifier


class WatchdogCliTests(unittest.TestCase):
    def setUp(self) -> None:
        for key in (
            'HERMES_HOME',
            'HERMES_WATCHDOG_JOB_ID',
            'HERMES_WATCHDOG_STALE_MINUTES',
            'HERMES_WATCHDOG_PRUNE_INTERVAL_MINUTES',
            'HERMES_WATCHDOG_PRUNE_OLDER_THAN',
            'HERMES_WATCHDOG_TELEGRAM_CHAT_ID',
            'TELEGRAM_BOT_TOKEN',
            'KLINIK_WORKDIR',
        ):
            os.environ.pop(key, None)

    def test_builds_watchdog_from_env(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        env_path = root / '.env'
        env_path.write_text(
            '\n'.join(
                [
                    'HERMES_HOME=' + str(root / 'hermes'),
                    'HERMES_WATCHDOG_JOB_ID=job123',
                    'HERMES_WATCHDOG_STALE_MINUTES=7',
                    'HERMES_WATCHDOG_TELEGRAM_CHAT_ID=101',
                    'TELEGRAM_BOT_TOKEN=token123',
                    'KLINIK_WORKDIR=' + str(root / 'klinik'),
                ]
            ),
            encoding='utf-8',
        )

        watchdog = build_watchdog_from_env(env_path)

        self.assertEqual(watchdog.job_id, 'job123')
        self.assertEqual(watchdog.stale_minutes, 7.0)
        self.assertEqual(watchdog.prune_interval_minutes, 360.0)
        self.assertEqual(watchdog.prune_older_than, '1d')
        self.assertEqual(watchdog.state_path, root / 'hermes' / 'watchdog' / 'state.json')
        self.assertIsInstance(watchdog.notifier, TelegramNotifier)

    def test_builds_prune_settings_from_env(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        env_path = root / '.env'
        env_path.write_text(
            '\n'.join(
                [
                    'HERMES_HOME=' + str(root / 'hermes'),
                    'HERMES_WATCHDOG_PRUNE_INTERVAL_MINUTES=90',
                    'HERMES_WATCHDOG_PRUNE_OLDER_THAN=7d',
                ]
            ),
            encoding='utf-8',
        )

        watchdog = build_watchdog_from_env(env_path)

        self.assertEqual(watchdog.prune_interval_minutes, 90.0)
        self.assertEqual(watchdog.prune_older_than, '7d')

    def test_command_runner_resolves_windows_binary(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        env_path = root / '.env'
        env_path.write_text('HERMES_HOME=' + str(root / 'hermes'), encoding='utf-8')
        watchdog = build_watchdog_from_env(env_path)
        commands = []
        original_run = watchdog_cli.subprocess.run
        original_which = watchdog_cli.shutil.which

        watchdog_cli.shutil.which = lambda command: str(root / 'hermes.CMD') if command == 'hermes' else None

        def fake_run(command: list[str], **kwargs: object) -> object:
            commands.append(command)
            return SimpleNamespace(returncode=0)

        watchdog_cli.subprocess.run = fake_run
        self.addCleanup(setattr, watchdog_cli.subprocess, 'run', original_run)
        self.addCleanup(setattr, watchdog_cli.shutil, 'which', original_which)

        watchdog.command_runner(['hermes', 'sessions', 'prune'], 10)

        self.assertEqual(commands, [[str(root / 'hermes.CMD'), 'sessions', 'prune']])
