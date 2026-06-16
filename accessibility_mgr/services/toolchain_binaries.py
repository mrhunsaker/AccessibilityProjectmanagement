"""Production accessibility binary integrations.

Provides executable wrappers for:
- DAISY Ace CLI
- EPUBCheck
- Liblouis braille translation (lou_translate / file2brl)

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

    def run_liblouis_translation(
        self,
        source_path: str,
        *,
        table: str = "en-ueb-g2.ctb",
        use_file2brl: bool = True,
    ) -> dict:
        """Translate *source_path* to BRF using Liblouis.

        STUB-027: Previously this method did not exist; calls fell through to
        the generic QAService which always returned a stub echo result.  This
        implementation uses the real ``file2brl`` (preferred) or
        ``lou_translate`` binary.

        Parameters
        ----------
        source_path:
            Path to the plain-text or formatted source document.
        table:
            Liblouis braille table name (default: en-ueb-g2.ctb for UEB grade 2).
        use_file2brl:
            When True (default), use ``file2brl`` which handles formatting.
            When False, fall back to ``lou_translate`` for raw cell output.

        Returns a dict with keys ``status``, ``output_path``, and
        ``execution`` (the raw ToolExecutionResult dict).
        """
        # Prefer file2brl for full-document translation; fall back to lou_translate
        binary_name = "file2brl" if use_file2brl else "lou_translate"
        binary = self.discover_binary(binary_name)
        if not binary and use_file2brl:
            binary_name = "lou_translate"
            binary = self.discover_binary("lou_translate")

        if not binary:
            return {
                "status": "unavailable",
                "reason": (
                    "Neither 'file2brl' nor 'lou_translate' found on PATH. "
                    "Install liblouis (https://liblouis.io) and ensure the "
                    "binaries are accessible."
                ),
            }

        src  = Path(source_path)
        brf  = Path(tempfile.mkdtemp(prefix="liblouis-")) / (src.stem + ".brf")

        if binary_name == "file2brl":
            command = [binary, "-t", table, str(src), str(brf)]
        else:
            # lou_translate writes to stdout; redirect in the command template
            command = [binary, "-f", table, str(src)]

        result: ToolExecutionResult = self.toolchain.execute(
            tool_name="Liblouis",
            command=command,
            artifact_paths=[str(brf)],
        )

        # For lou_translate, stdout IS the BRF content
        if binary_name == "lou_translate" and result.status == "completed" and result.stdout:
            brf.write_text(result.stdout, encoding="utf-8")

        return {
            "status": result.status,
            "output_path": str(brf) if brf.exists() else None,
            "execution": asdict(result),
        }


__all__ = [
    "AccessibilityBinaryIntegrationService",
]
