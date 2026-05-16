"""Production accessibility binary integrations.

Provides executable wrappers for:
- DAISY Ace CLI
- EPUBCheck

This layer extends the existing subprocess abstraction with:
- binary discovery
- secure invocation
- artifact output directories
- structured execution contracts
"""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import asdict
from pathlib import Path

from .toolchain import (
    AccessibilityToolchainService,
    ToolExecutionResult,
)


class AccessibilityBinaryIntegrationService:
    """Production binary integration service."""

    def __init__(
        self,
        toolchain: AccessibilityToolchainService | None = None,
    ) -> None:
        self.toolchain = toolchain or AccessibilityToolchainService(
            timeout_seconds=300,
        )

    def discover_binary(self, binary_name: str) -> str | None:
        return shutil.which(binary_name)

    def run_daisy_ace(
        self,
        epub_path: str,
    ) -> dict:
        binary = self.discover_binary("ace")

        if not binary:
            return {
                "status": "unavailable",
                "reason": "DAISY Ace CLI binary not installed",
            }

        output_dir = tempfile.mkdtemp(prefix="ace-output-")

        command = [
            binary,
            epub_path,
            "--outdir",
            output_dir,
            "--force",
        ]

        result: ToolExecutionResult = self.toolchain.execute(
            tool_name="DAISY Ace",
            command=command,
            artifact_paths=[output_dir],
        )

        return {
            "execution": asdict(result),
            "output_directory": output_dir,
        }

    def run_epubcheck(
        self,
        epub_path: str,
    ) -> dict:
        binary = self.discover_binary("epubcheck")

        if not binary:
            return {
                "status": "unavailable",
                "reason": "EPUBCheck binary not installed",
            }

        report_path = Path(tempfile.mktemp(suffix=".xml"))

        command = [
            binary,
            epub_path,
            "-out",
            str(report_path),
        ]

        result: ToolExecutionResult = self.toolchain.execute(
            tool_name="EPUBCheck",
            command=command,
            artifact_paths=[str(report_path)],
        )

        return {
            "execution": asdict(result),
            "report_path": str(report_path),
        }


__all__ = [
    "AccessibilityBinaryIntegrationService",
]
