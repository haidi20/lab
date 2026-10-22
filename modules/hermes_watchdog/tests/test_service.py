from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from modules.hermes_watchdog.service import HermesWatchdog


class CompletedProcess:
    returncode = 0
    stdout = 'ok'
    stderr = ''


class HermesWatchdogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.log_path = self.root / 'agent.log'
        self.state_path = self.root / 'state.json'
        self.commands = []
        self.messages = []
        self.current = datetime(2026, 10, 22, 18, 45)

    def write_log(self, content: str) -> None:
        self.log_path.write_text(content, encoding='utf-8')

    def read_cron(self) -> dict[str, object]:
        return {
            'jobs': [
                {
                    'id': 'job123',
                    'name': 'Trello Todo Worker',
                    'enabled': True,
                    'state': 'scheduled',
                    'last_run_at': '2026-10-22T18:00:00',
                }
            ]
        }

    def read_empty_status(self) -> str:
        return ''

    def get_current(self) -> datetime:
        return self.current

    def completed_process(self) -> object:
        return CompletedProcess()

    def capture_command(self, command: list[str], timeout: float) -> object:
        self.commands.append(command)
        self.assertGreater(timeout, 0)
        return self.completed_process()

    def build(self, **overrides: object) -> HermesWatchdog:
        values = {
            'cron_reader': self.read_cron,
            'log_path': self.log_path,
            'git_status_reader': self.read_empty_status,
            'command_runner': self.capture_command,
            'notifier': self.messages.append,
            'now': self.get_current,
            'state_path': self.state_path,
            'stale_minutes': 15,
            'job_id': 'job123',
        }
        values.update(overrides)
        return HermesWatchdog(**values)

    def test_recent_patch_is_healthy_without_action(self) -> None:
        self.write_log('2026-10-22 18:29:00,000 INFO agent.tool_executor: tool patch completed')
        self.current = datetime(2026, 10, 22, 18, 40)
        result = self.build().check()

        self.assertEqual(result.status, 'healthy')
        self.assertEqual(self.commands, [self.expected_prune_command()])
        self.assertEqual(self.messages, [])

    def test_ended_sessions_are_pruned_once_per_interval(self) -> None:
        self.write_log('2026-10-22 18:44:00,000 INFO agent.tool_executor: tool patch completed')
        watchdog = self.build()

        self.current = datetime(2026, 10, 22, 18, 45)
        watchdog.check()

        self.assertEqual(self.commands, [self.expected_prune_command()])
        saved = json.loads(self.state_path.read_text(encoding='utf-8'))
        self.assertEqual(saved['last_prune_at'], '2026-10-22T18:45:00')

        self.write_log('2026-10-22 23:39:00,000 INFO agent.tool_executor: tool patch completed')
        self.current = datetime(2026, 10, 22, 23, 40)
        watchdog.check()
        self.assertEqual(len(self.commands), 1)

        self.write_log('2026-10-22 23:45:00,000 INFO agent.tool_executor: tool patch completed')
        self.current = datetime(2026, 10, 22, 23, 46)
        watchdog.check()
        self.assertEqual(self.commands[-1], self.expected_prune_command())

    def test_changed_git_status_counts_as_progress(self) -> None:
        self.write_log('2026-10-22 18:00:00,000 INFO agent.tool_executor: tool terminal completed')
        values = iter(['', 'M src/app.php'])
        watchdog = self.build(git_status_reader=lambda: next(values))

        self.current = datetime(2026, 10, 22, 18, 10)
        first = watchdog.check()
        self.current = datetime(2026, 10, 22, 18, 20)
        second = watchdog.check()

        self.assertEqual(first.status, 'healthy')
        self.assertEqual(second.status, 'healthy')
        self.assertEqual(self.commands, [self.expected_prune_command()])

    def test_first_stale_run_notifies_without_restarting(self) -> None:
        self.write_log('2026-10-22 18:00:00,000 INFO agent.tool_executor: tool terminal completed')
        self.current = datetime(2026, 10, 22, 19, 5)

        result = self.build().check()

        self.assertEqual(result.status, 'stale')
        self.assertEqual(result.action, 'notify')
        self.assertEqual(self.commands, [self.expected_prune_command()])
        self.assertEqual(len(self.messages), 1)
        self.assertIn('stale', self.messages[0].lower())

    def test_repeated_stale_run_restarts_gateway(self) -> None:
        self.write_log('2026-10-22 18:00:00,000 INFO agent.tool_executor: tool terminal completed')
        self.current = datetime(2026, 10, 22, 18, 20)
        watchdog = self.build()
        watchdog.check()

        self.current = datetime(2026, 10, 22, 19, 1)
        result = watchdog.check()

        self.assertEqual(result.status, 'stale')
        self.assertEqual(result.action, 'restart_gateway')
        self.assertEqual(len(self.commands), 2)
        self.assertEqual(self.commands[0], self.expected_prune_command())
        self.assertIn('gateway', self.commands[1])
        self.assertIn('restart', self.commands[1])

    def test_disabled_job_is_resumed_and_triggered(self) -> None:
        self.write_log('2026-10-22 18:29:00,000 INFO agent.tool_executor: tool patch completed')

        def read_paused_cron() -> dict[str, object]:
            return {
                'jobs': [
                    {
                        'id': 'job123',
                        'name': 'Trello Todo Worker',
                        'enabled': False,
                        'state': 'paused',
                    }
                ]
            }

        result = self.build(cron_reader=read_paused_cron).check()

        self.assertEqual(result.status, 'paused')
        self.assertEqual(result.action, 'resume_job')
        self.assertEqual(len(self.commands), 3)
        self.assertEqual(self.commands[0][-3:], ['cron', 'resume', 'job123'])
        self.assertEqual(self.commands[1][-3:], ['cron', 'run', 'job123'])
        self.assertEqual(self.commands[2], self.expected_prune_command())

    def expected_prune_command(self) -> list[str]:
        return ['hermes', 'sessions', 'prune', '--older-than', '1d', '--yes']

    def test_state_is_loaded_and_saved(self) -> None:
        self.state_path.write_text(json.dumps({'nudge_count': 1, 'git_fingerprint': ''}), encoding='utf-8')
        self.write_log('2026-10-22 18:00:00,000 INFO agent.tool_executor: tool terminal completed')
        self.current = datetime(2026, 10, 22, 18, 16)

        result = self.build().check()

        self.assertEqual(result.action, 'restart_gateway')
        saved = json.loads(self.state_path.read_text(encoding='utf-8'))
        self.assertEqual(saved['nudge_count'], 0)
        self.assertEqual(saved['restart_count'], 1)
