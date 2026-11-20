from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any, Mapping


class GatewayJobError(RuntimeError):
    """Raised when a Gateway sync job cannot be started or queried."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class GatewayJobManager:
    """Run one background Gateway sync per scope while keeping status in memory."""

    def __init__(self, service: Any) -> None:
        self.service = service
        self._condition = threading.Condition()
        self._jobs: dict[str, dict[str, Any]] = {}
        self._threads: dict[str, threading.Thread] = {}

    def start(
        self,
        scope: str,
        params: Mapping[str, Any] | None = None,
        *,
        force: bool = False,
    ) -> dict[str, Any]:
        self._validate_scope(scope)
        with self._condition:
            current = self._jobs.get(scope)
            if current and current.get("status") in {"queued", "running"}:
                raise GatewayJobError("job_aktif", f"Sync {scope} is already running")

            state: dict[str, Any] = {
                "scope": scope,
                "status": "running",
                "params": dict(params or {}),
                "force": force,
                "created_at": _utc_now(),
                "started_at": _utc_now(),
                "finished_at": None,
                "items": 0,
                "pages": 0,
                "error_code": None,
                "error_message": None,
            }
            self._jobs[scope] = state
            thread = threading.Thread(
                target=self._run,
                args=(scope, dict(params or {}), force),
                name=f"inaproc-gateway-{scope}",
                daemon=True,
            )
            self._threads[scope] = thread
            thread.start()
            return dict(state)

    def status(self, scope: str) -> dict[str, Any]:
        self._validate_scope(scope)
        with self._condition:
            state = self._jobs.get(scope)
            if state is None:
                return {"scope": scope, "status": "idle"}
            return dict(state)

    def wait(self, scope: str, timeout: float = 5.0) -> dict[str, Any]:
        self._validate_scope(scope)
        with self._condition:
            self._condition.wait_for(
                lambda: self._jobs.get(scope, {}).get("status")
                in {"success", "skipped", "failed"},
                timeout=timeout,
            )
            state = self._jobs.get(scope)
            if state is None:
                return {"scope": scope, "status": "idle"}
            return dict(state)

    def _run(self, scope: str, params: dict[str, Any], force: bool) -> None:
        with self._condition:
            state = self._jobs[scope]
            state["status"] = "running"
            state["started_at"] = _utc_now()
            self._condition.notify_all()

        try:
            result = self.service.sync(scope, params, force=force)
            final = dict(result) if isinstance(result, Mapping) else {}
            final.setdefault("scope", scope)
            final.setdefault("status", "success")
        except Exception as exc:  # Keep the worker alive; expose a safe failure state.
            final = {
                "scope": scope,
                "status": "failed",
                "items": 0,
                "error_code": getattr(exc, "code", "SYNC_FAILED"),
                "error_message": str(exc),
            }

        with self._condition:
            state = self._jobs[scope]
            state.update(final)
            state["status"] = str(final.get("status") or "failed")
            state["finished_at"] = _utc_now()
            if state["status"] == "failed" and not state.get("error_message"):
                state["error_message"] = str(final.get("error_code") or "Gateway sync failed")
            self._condition.notify_all()

    @staticmethod
    def _validate_scope(scope: str) -> None:
        from modules.inaproc.api.gateway_sync import SCOPES

        if scope not in SCOPES:
            raise GatewayJobError("scope_tidak_valid", f"Unsupported scope: {scope}")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
