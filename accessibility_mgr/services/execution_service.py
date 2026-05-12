"""
Execution service — runs external tool commands via subprocess.

Used by QA tooling and pipeline orchestration.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class ExecutionResult:
    """ExecutionResult class.
    
    """
    command: str
    success: bool
    output: str
    return_code: int


class ExecutionService:
    """ExecutionService class.
    
    """
    DEFAULT_TIMEOUT: int = 120  # seconds

    @staticmethod
    def run_command(
        command: list[str],
        timeout: int = 120,
        cwd: Optional[str] = None,
    ) -> ExecutionResult:
        """Run a shell command and return the full result."""
        cmd_str = " ".join(command)
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                cwd=cwd,
            )
            output = result.stdout or ""
            if result.stderr:
                output = output + ("\n" if output else "") + result.stderr
            return ExecutionResult(
                command=cmd_str,
                success=result.returncode == 0,
                output=output.strip(),
                return_code=result.returncode,
            )
        except FileNotFoundError:
            return ExecutionResult(
                command=cmd_str,
                success=False,
                output=(
                    f"Command not found: '{command[0]}'. "
                    "Is the tool installed and on PATH?"
                ),
                return_code=-1,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                command=cmd_str,
                success=False,
                output=f"Command timed out after {timeout} seconds.",
                return_code=-2,
            )
        except Exception as exc:
            return ExecutionResult(
                command=cmd_str,
                success=False,
                output=f"Unexpected error: {exc}",
                return_code=-3,
            )

    @staticmethod
    def check_tool_available(tool_name: str) -> bool:
        """Return True if the named executable can be found on PATH."""
        result = ExecutionService.run_command(["which", tool_name], timeout=5)
        if not result.success:
            result = ExecutionService.run_command(["where", tool_name], timeout=5)
        return result.success
