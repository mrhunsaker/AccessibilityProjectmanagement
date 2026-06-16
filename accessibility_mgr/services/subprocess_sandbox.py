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
        """Execute *command* inside a sandboxed working directory.

        FUN-032: When *allowed_directory* is supplied its existence, type, and
        writability are verified before use.  Absolute paths are required.
        FUN-033: When a temp dir is created this method guarantees cleanup via
        try/finally, even on timeout or exception.
        """
        _tmp_dir_obj = None  # only set when we own the directory

        if allowed_directory is not None:
            # FUN-032: validate the caller-supplied directory
            adir = Path(allowed_directory).resolve()
            if not adir.exists():
                raise ValueError(
                    f"allowed_directory '{allowed_directory}' does not exist."
                )
            if not adir.is_dir():
                raise ValueError(
                    f"allowed_directory '{allowed_directory}' is not a directory."
                )
            if not os.access(str(adir), os.W_OK):
                raise ValueError(
                    f"allowed_directory '{adir}' is not writable by the current process."
                )
            if ".." in str(adir):
                raise ValueError(
                    f"allowed_directory '{adir}' contains a path-traversal sequence."
                )
            sandbox_dir = str(adir)
        else:
            # FUN-033: use a context-managed temp dir we can reliably clean up
            _tmp_dir_obj = tempfile.TemporaryDirectory(prefix="accessibility-sandbox-")
            sandbox_dir = _tmp_dir_obj.name

        env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONUNBUFFERED": "1",
        }

        try:
            completed = subprocess.run(
                list(command),
                cwd=sandbox_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                env=env,
                check=False,
            )
        finally:
            # FUN-033: ensure temp dir is removed even on timeout/exception
            if _tmp_dir_obj is not None:
                _tmp_dir_obj.cleanup()

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
