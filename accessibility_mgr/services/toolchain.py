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

import json
import subprocess
import tempfile
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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

    def run_mock_ace(self, epub_path: str) -> dict[str, Any]:
        """Representative DAISY Ace integration stub."""

        with tempfile.NamedTemporaryFile(
            suffix=".json",
            delete=False,
        ) as report:
            payload = {
                "tool": "daisy-ace",
                "epub": epub_path,
                "score": 98,
                "violations": [],
            }

            report.write(json.dumps(payload).encode("utf-8"))
            report.flush()

            result = self.execute(
                tool_name="DAISY Ace",
                command=["echo", "Simulated DAISY Ace Execution"],
                artifact_paths=[report.name],
            )

            return {
                "execution": asdict(result),
                "report_path": report.name,
            }

    def run_mock_epubcheck(self, epub_path: str) -> dict[str, Any]:
        """Representative EPUBCheck integration stub."""

        with tempfile.NamedTemporaryFile(
            suffix=".xml",
            delete=False,
        ) as report:
            report.write(
                b"<epubcheck status='passed'></epubcheck>"
            )
            report.flush()

            result = self.execute(
                tool_name="EPUBCheck",
                command=["echo", "Simulated EPUBCheck Execution"],
                artifact_paths=[report.name],
            )

            return {
                "execution": asdict(result),
                "report_path": report.name,
            }


__all__ = [
    "AccessibilityToolchainService",
    "ToolExecutionResult",
]
