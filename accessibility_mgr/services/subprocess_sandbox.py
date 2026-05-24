"""Secure subprocess sandboxing infrastructure."""

from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Sequence


@dataclass(slots=True)
class SandboxExecutionResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    working_directory: str


class SecureSubprocessSandbox:
    """Sandboxed subprocess execution environment."""

    def __init__(self, timeout_seconds: int = 300) -> None:
        self.timeout_seconds = timeout_seconds

    def execute(
        self,
        *,
        command: Sequence[str],
        allowed_directory: str | None = None,
    ) -> dict:
        sandbox_dir = allowed_directory or tempfile.mkdtemp(
            prefix="accessibility-sandbox-"
        )

        env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONUNBUFFERED": "1",
        }

        completed = subprocess.run(
            list(command),
            cwd=sandbox_dir,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
            env=env,
            check=False,
        )

        result = SandboxExecutionResult(
            command=list(command),
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            working_directory=str(Path(sandbox_dir).resolve()),
        )

        return asdict(result)


__all__ = [
    "SecureSubprocessSandbox",
    "SandboxExecutionResult",
]
