from __future__ import annotations

import subprocess
import signal
import sys
import time
from collections.abc import Callable

class Supervisor:
    def __init__(self, command: list[str], max_restarts: int = 5, max_restart_delay: float = 30.0) -> None:
        self.command = command
        self.max_restarts = max_restarts
        self.max_restart_delay = max_restart_delay
        self.healthy_seconds = 60.0

    def run(
        self,
        spawn: Callable[[list[str]], object] | None = None,
        sleep: Callable[[float], None] | None = None,
        restart_delay: float = 1.0,
        healthy_seconds: float | None = None,
        max_restart_delay: float | None = None,
    ) -> None:
        spawn = spawn or self._spawn
        sleep = sleep or time.sleep
        if healthy_seconds is not None:
            self.healthy_seconds = healthy_seconds
        if max_restart_delay is not None:
            self.max_restart_delay = max_restart_delay
        restarts = 0
        current_process = None

        def stop_current_process(signum, frame) -> None:
            if current_process is not None and hasattr(current_process, "terminate"):
                current_process.terminate()

        for signal_number in (signal.SIGTERM, signal.SIGINT):
            try:
                signal.signal(signal_number, stop_current_process)
            except ValueError:
                pass
        while True:
            started_at = time.monotonic()
            try:
                process = spawn(self.command)
                current_process = process
            except (OSError, subprocess.SubprocessError) as error:
                if restarts >= self.max_restarts:
                    return
                restarts += 1
                print(f"Bot spawn failed, retrying: {error}", flush=True)
                sleep(restart_delay)
                continue
            returncode = getattr(process, "wait", lambda: 0)()
            if returncode == 0:
                return
            if returncode in (-15, 130):
                return
            if time.monotonic() - started_at >= self.healthy_seconds:
                restarts = 0
            if restarts >= self.max_restarts:
                return
            restarts += 1
            sleep(min(restart_delay * (2 ** (restarts - 1)), self.max_restart_delay))

    def configure(self, healthy_seconds: float) -> None:
        self.healthy_seconds = healthy_seconds

    def _spawn(self, command: list[str]) -> subprocess.Popen[bytes]:
        return subprocess.Popen(command)


def main() -> None:
    import os

    max_restarts = int(os.environ.get("TELEGRAM_STORE_MAX_RESTARTS", "5"))
    supervisor = Supervisor([sys.executable, "-m", "modules.telegram_store"], max_restarts=max_restarts)
    supervisor.configure(float(os.environ.get("TELEGRAM_STORE_HEALTHY_SECONDS", "60")))
    supervisor.run()
