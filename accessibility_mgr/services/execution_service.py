from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    command: str
    success: bool
    output: str


class ExecutionService:
    @staticmethod
    def run_command(command: list[str]) -> ExecutionResult:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )

            return ExecutionResult(
                command=" ".join(command),
                success=result.returncode == 0,
                output=result.stdout or result.stderr,
            )

        except Exception as exc:
            return ExecutionResult(
                command=" ".join(command),
                success=False,
                output=str(exc),
            )
