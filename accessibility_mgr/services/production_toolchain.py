"""Production-grade accessibility toolchain execution.

Provides hardened integrations for:
- DAISY Ace
- EPUBCheck
- DAISY Pipeline

Features:
- command validation
- subprocess isolation
- artifact registration
- execution telemetry
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from .toolchain import (
    AccessibilityToolchainService,
    ToolExecutionResult,
)
from .toolchain_security import ToolchainSecurityService


class ProductionToolchainService:
    """Hardened accessibility toolchain execution service."""

    def __init__(self) -> None:
        self.executor = AccessibilityToolchainService(
            timeout_seconds=120,
        )
        self.security = ToolchainSecurityService()

    def execute_secure(
        self,
        *,
        tool_name: str,
        command: list[str],
        artifact_paths: list[str] | None = None,
    ) -> dict[str, Any]:
        if not self.security.validate_command(
            tool_name=tool_name,
            command=command,
        ):
            return {
                "status": "rejected",
                "reason": "Command not permitted",
            }

        result = self.executor.execute(
            tool_name=tool_name,
            command=command,
            artifact_paths=artifact_paths,
        )

        registered = []

        for artifact in artifact_paths or []:
            registered.append(
                asdict(
                    self.security.register_artifact(
                        path=artifact,
                        classification="qa-report",
                    )
                )
            )

        return {
            "status": "completed",
            "execution": asdict(result),
            "registered_artifacts": registered,
        }

    def run_ace(
        self,
        *,
        epub_path: str,
    ) -> dict[str, Any]:
        report_path = f"{Path(epub_path).stem}_ace_report.json"

        return self.execute_secure(
            tool_name="ace",
            command=["node", "ace", epub_path],
            artifact_paths=[report_path],
        )

    def run_epubcheck(
        self,
        *,
        epub_path: str,
    ) -> dict[str, Any]:
        report_path = (
            f"{Path(epub_path).stem}_epubcheck_report.xml"
        )

        return self.execute_secure(
            tool_name="epubcheck",
            command=["java", "epubcheck", epub_path],
            artifact_paths=[report_path],
        )


__all__ = ["ProductionToolchainService"]
