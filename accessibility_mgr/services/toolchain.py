"""Accessibility toolchain integration layer.

Provides subprocess execution wrappers for:
- DAISY Ace
- EPUBCheck
- DAISY Pipeline

This layer standardizes:
- timeout handling
- artifact capture
- execution isolation
- structured results
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(slots=True)
class ToolExecutionResult:
    tool_name: str
    command: list[str]
    status: str
    exit_code: int
    stdout: str
    stderr: str
    artifacts: list[str]
    executed_at: str


class AccessibilityToolchainService:
    """Accessibility subprocess execution service."""

    def __init__(self, *, timeout_seconds: int = 60) -> None:
        self.timeout_seconds = timeout_seconds

    def execute(
        self,
        *,
        tool_name: str,
        command: list[str],
        artifact_paths: list[str] | None = None,
    ) -> ToolExecutionResult:
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )

            status = (
                "completed"
                if completed.returncode == 0
                else "failed"
            )

            return ToolExecutionResult(
                tool_name=tool_name,
                command=command,
                status=status,
                exit_code=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
                artifacts=artifact_paths or [],
                executed_at=datetime.now(timezone.utc).isoformat(),
            )

        except subprocess.TimeoutExpired as exc:
            return ToolExecutionResult(
                tool_name=tool_name,
                command=command,
                status="timeout",
                exit_code=-1,
                stdout=exc.stdout or "",
                stderr=exc.stderr or "Execution timed out",
                artifacts=[],
                executed_at=datetime.now(timezone.utc).isoformat(),
            )

    # AUDIT-FIX-001: run_mock_ace() / run_mock_epubcheck() were removed from
    # this class.  They never invoked DAISY Ace or EPUBCheck — they wrote a
    # hardcoded "score: 98, violations: []" payload and ran `echo` as the
    # "command", so any caller always saw a fabricated passing result.
    # Real DAISY Ace / EPUBCheck / Liblouis execution now lives in
    # AccessibilityBinaryIntegrationService (services/toolchain_binaries.py),
    # which discovers the real binary on PATH and reports "unavailable"
    # honestly instead of faking success. See ui/toolchain_dashboard.py.


__all__ = [
    "AccessibilityToolchainService",
    "ToolExecutionResult",
]
