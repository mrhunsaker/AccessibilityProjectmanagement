"""
QA service — accessibility validation tool registry and execution.

Changes applied (see fix_specs.json):
  FIX-012  When job_type and job_id are provided, a QA_RUN event is written
           to the job's metadata_event record in addition to qa_run table.
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass, field
from typing import Optional

from ..db import queries as Q
from .execution_service import ExecutionResult, ExecutionService


@dataclass
class QATool:
    name: str
    domain: str
    description: str
    executable: str
    command_template: str
    timeout: int = 120

    def build_command(self, input_path: str = "") -> list[str]:
        cmd = self.command_template.replace("{input}", input_path)
        return shlex.split(cmd)

    def is_available(self) -> bool:
        return ExecutionService.check_tool_available(self.executable)


QA_TOOLS: list[QATool] = [
    QATool(
        name="DAISY Ace",
        domain="EPUB Accessibility",
        description="WCAG and EPUB accessibility validation (DAISY Ace)",
        executable="ace",
        command_template="ace {input} -o ace-report",
        timeout=180,
    ),
    QATool(
        name="EPUBCheck",
        domain="EPUB Validation",
        description="Structural EPUB conformance validation",
        executable="epubcheck",
        command_template="epubcheck {input}",
        timeout=60,
    ),
    QATool(
        name="Liblouis",
        domain="Braille QA",
        description="Braille translation verification via file2brl",
        executable="file2brl",
        command_template="file2brl {input}",
        timeout=60,
    ),
    QATool(
        name="BRLTTY",
        domain="Braille Device QA",
        description="Braille hardware interaction validation",
        executable="brltty",
        command_template="brltty --help",
        timeout=10,
    ),
    QATool(
        name="Pandoc",
        domain="Document QA",
        description="Document conversion and format verification",
        executable="pandoc",
        command_template="pandoc --version",
        timeout=10,
    ),
    QATool(
        name="ANZAGG Validation",
        domain="3D Accessibility",
        description=(
            "Tactile and accessible 3-D print review. "
            "ANZAGG covers tactile readability standards, educational object review, "
            "and tactile pedagogy validation. Manual review workflow."
        ),
        executable="echo",
        command_template="echo ANZAGG validation requires manual tactile review of: {input}",
        timeout=5,
    ),
]

_TOOL_MAP: dict[str, QATool] = {t.name: t for t in QA_TOOLS}


class QAService:
    """Service for listing and executing QA tooling commands."""

    @staticmethod
    def list_tools() -> list[QATool]:
        return QA_TOOLS

    @staticmethod
    def get_tool(name: str) -> Optional[QATool]:
        return _TOOL_MAP.get(name)

    @staticmethod
    def run_tool(
        name: str,
        input_path: str = "",
        job_type: Optional[str] = None,
        job_id: Optional[int] = None,
    ) -> ExecutionResult:
        """Execute a QA tool, persist the result, and return it.

        FIX-012: When job_type and job_id are provided, a QA_RUN event is
        also written to the job's metadata_event record so the result appears
        in the job's audit trail.
        """
        tool = _TOOL_MAP.get(name)
        if tool is None:
            return ExecutionResult(
                command=name,
                success=False,
                output=f"Unknown QA tool: '{name}'",
                return_code=-1,
            )

        command = tool.build_command(input_path)
        result = ExecutionService.run_command(command, timeout=tool.timeout)

        # Persist to qa_run table
        Q.log_qa_run(
            tool_name=name,
            command=result.command,
            success=result.success,
            output=result.output,
            job_type=job_type,
            job_id=job_id,
        )

        # FIX-012: also write to the job's event log when linked to a job
        if job_type and job_id:
            Q.log_event(
                job_type, job_id,
                "QA_RUN",
                "SUCCESS" if result.success else "FAILURE",
                agent="system",
                detail=f"{name}: {'PASS' if result.success else 'FAIL'}",
                extra_metadata={
                    "tool": name,
                    "command": result.command,
                    "output_preview": result.output[:500] if result.output else "",
                },
            )

        return result
