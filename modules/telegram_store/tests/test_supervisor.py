from __future__ import annotations

import unittest

import sys
import threading
import time
from unittest.mock import patch

from modules.telegram_store.supervisor import Supervisor
from modules.telegram_store import supervisor as supervisor_module


class FakeProcess:
    def __init__(self, returncode: int) -> None:
        self.returncode = returncode

    def wait(self) -> int:
        return self.returncode


class SupervisorTests(unittest.TestCase):
    def test_restarts_after_nonzero_exit_until_success(self) -> None:
        process_requests: list[list[str]] = []
        waits = iter([1, 1, 0])
        delays: list[float] = []

        def spawn(command: list[str]) -> FakeProcess:
            process_requests.append(command)
            return FakeProcess(next(waits))

        supervisor = Supervisor(["python", "-m", "modules.telegram_store"])
        supervisor.run(spawn=spawn, sleep=delays.append, restart_delay=3)

        self.assertEqual(3, len(process_requests))
        self.assertEqual(["python", "-m", "modules.telegram_store"], process_requests[0])
        self.assertEqual([3, 6], delays)

    def test_exits_successfully_without_restart(self) -> None:
        spawn_calls = 0

        def spawn(command: list[str]) -> FakeProcess:
            nonlocal spawn_calls
            spawn_calls += 1
            return FakeProcess(0)

        Supervisor(["python", "-m", "modules.telegram_store"]).run(spawn=spawn, sleep=lambda seconds: None)

        self.assertEqual(1, spawn_calls)

    def test_stops_after_reaching_restart_limit(self) -> None:
        spawn_calls = 0
        delays: list[float] = []

        def spawn(command: list[str]) -> FakeProcess:
            nonlocal spawn_calls
            spawn_calls += 1
            return FakeProcess(1)

        Supervisor(["sleep", "0"], max_restarts=2).run(
            spawn=spawn,
            sleep=delays.append,
            restart_delay=0,
            healthy_seconds=0.005,
        )

        self.assertEqual(3, spawn_calls)
        self.assertEqual([0, 0], delays)

    def test_reset_restart_budget_after_process_stays_healthy(self) -> None:
        process_specs = [(0.0, 1), (0.02, 1), (0.0, 1), (0.0, 1)]
        delays: list[float] = []
        spawn_calls = 0

        def spawn(command: list[str]) -> FakeProcess:
            nonlocal spawn_calls
            spawn_calls += 1
            duration, returncode = process_specs[spawn_calls - 1]
            time.sleep(duration)
            return FakeProcess(returncode)

        Supervisor(["sleep", "0"], max_restarts=2).run(
            spawn=spawn,
            sleep=delays.append,
            restart_delay=0,
            healthy_seconds=0.005,
        )

        self.assertEqual(4, spawn_calls)

    def test_main_runs_supervisor_when_enabled(self) -> None:
        calls: list[object] = []

        class FakeSupervisor:
            def __init__(self, command: list[str], max_restarts: int) -> None:
                calls.append((command, max_restarts))

            def configure(self, healthy_seconds: float) -> None:
                calls.append(healthy_seconds)

            def run(self) -> None:
                calls.append("run")

        original_supervisor = supervisor_module.Supervisor
        supervisor_module.Supervisor = FakeSupervisor
        try:
            supervisor_module.main()
        finally:
            supervisor_module.Supervisor = original_supervisor

        self.assertEqual([([sys.executable, "-m", "modules.telegram_store"], 5), 60.0, "run"], calls)

    def test_spawn_error_is_retried_until_bot_can_start(self) -> None:
        spawn_calls = 0
        delays: list[float] = []

        def spawn(command: list[str]) -> FakeProcess:
            nonlocal spawn_calls
            spawn_calls += 1
            if spawn_calls < 3:
                raise FileNotFoundError("temporary spawn failure")
            return FakeProcess(0)

        Supervisor(["bot"], max_restarts=2).run(
            spawn=spawn,
            sleep=delays.append,
            restart_delay=0,
        )

        self.assertEqual(3, spawn_calls)
        self.assertEqual([0, 0], delays)

    def test_spawn_error_respects_restart_limit(self) -> None:
        spawn_calls = 0
        delays: list[float] = []

        def spawn(command: list[str]) -> FakeProcess:
            nonlocal spawn_calls
            spawn_calls += 1
            raise FileNotFoundError("spawn unavailable")

        Supervisor(["bot"], max_restarts=2).run(
            spawn=spawn,
            sleep=delays.append,
            restart_delay=0,
        )

        self.assertEqual(3, spawn_calls)
        self.assertEqual([0, 0], delays)

    def test_restart_delay_grows_and_is_capped_after_consecutive_failures(self) -> None:
        spawn_calls = 0
        delays: list[float] = []

        def spawn(command: list[str]) -> FakeProcess:
            nonlocal spawn_calls
            spawn_calls += 1
            return FakeProcess(1)

        Supervisor(["bot"], max_restarts=4).run(
            spawn=spawn,
            sleep=delays.append,
            restart_delay=1,
            max_restart_delay=3,
        )

        self.assertEqual(5, spawn_calls)
        self.assertEqual([1, 2, 3, 3], delays)

    def test_termination_signal_stops_supervisor_without_restart(self) -> None:
        spawn_calls = 0
        delays: list[float] = []

        def spawn(command: list[str]) -> FakeProcess:
            nonlocal spawn_calls
            spawn_calls += 1
            return FakeProcess(-15)

        Supervisor(["bot"], max_restarts=5).run(
            spawn=spawn,
            sleep=delays.append,
            restart_delay=0,
        )

        self.assertEqual(1, spawn_calls)
        self.assertEqual([], delays)

    def test_supervisor_forwards_signal_to_running_child(self) -> None:
        class SlowChild:
            def __init__(self) -> None:
                self.terminate_calls = 0

            def terminate(self) -> None:
                self.terminate_calls += 1

            def wait(self) -> int:
                time.sleep(0.03)
                return -15

        child = SlowChild()

        def spawn(command: list[str]) -> SlowChild:
            return child

        with patch('modules.telegram_store.supervisor.signal.signal') as register_signal:
            def send_signal() -> None:
                handler = register_signal.call_args_list[0][0][1]
                handler(15, None)

            timer = threading.Timer(0.01, send_signal)
            timer.start()

            Supervisor(["bot"]).run(
                spawn=spawn,
                sleep=lambda seconds: None,
                restart_delay=0,
            )
            timer.join()

        self.assertEqual(1, child.terminate_calls)
