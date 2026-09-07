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
    manual_review: bool = False  # When True, no CLI runs — reviewer fills a form

    def build_command(self, input_path: str = "") -> list[str]:
        cmd = self.command_template.replace("{input}", input_path)
        return shlex.split(cmd)

    def is_available(self) -> bool:
        if self.manual_review:
            return True  # manual tools are always "available"
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
        name="GLOW (ACB Large Print)",
        domain="Large Print / Document QA",
        description=(
            "Audits Word, Excel, PowerPoint, Markdown, PDF and EPUB against the "
            "ACB Large Print Guidelines, Microsoft Accessibility Checker rules and "
            "WCAG 2.2 AA (Community-Access GLOW)."
        ),
        executable="acb-large-print",
        command_template="acb-large-print audit {input} --format json",
        timeout=180,
    ),
    QATool(
        name="ANZAGG Validation",
        domain="3D Accessibility",
        description=(
            "Tactile and accessible 3-D print review. "
            "ANZAGG covers tactile readability standards, educational object review, "
            "and tactile pedagogy validation. Manual review workflow — "
            "no CLI tool exists; a reviewer fills in findings via a form."
        ),
        executable="",
        command_template="",
        timeout=0,
        manual_review=True,
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

        if tool.manual_review:
            # Manual-review tools have no CLI — the UI must route them to
            # the review form (qa.py _run_tool_dialog → manual branch).
            # If run_tool is called for one anyway, surface an honest error
            # rather than running echo and recording a fake SUCCESS.
            return ExecutionResult(
                command="(manual review — no CLI)",
                success=False,
                output=(
                    f"'{name}' is a manual-review workflow with no CLI tool. "
                    "Use the 'Record Manual Review' form to submit findings."
                ),
                return_code=-2,
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

    @staticmethod
    def log_manual_qa_review(
        tool_name: str,
        asset_path: str,
        passed: bool,
        reviewer: str,
        notes: str,
        job_type: Optional[str] = None,
        job_id: Optional[int] = None,
    ) -> None:
        """Persist a manual QA review finding to qa_run and optionally to a job's event log.

        Used by the 'Record Manual Review' form for tools where no CLI
        exists (manual_review=True), such as ANZAGG Validation. Writing a
        real record here replaces the previous behavior of running `echo`
        and fabricating a SUCCESS result.
        """
        outcome = "PASS" if passed else "FAIL"
        summary = f"Manual review by {reviewer or 'unknown'}: {outcome}. {notes}".strip()

        Q.log_qa_run(
            tool_name=tool_name,
            command="(manual review)",
            success=passed,
            output=summary,
            job_type=job_type,
            job_id=job_id,
        )

        if job_type and job_id:
            Q.log_event(
                job_type, job_id,
                "MANUAL_QA_REVIEW",
                "SUCCESS" if passed else "FAILURE",
                agent=reviewer or "reviewer",
                detail=f"{tool_name} manual review: {outcome}",
                extra_metadata={
                    "tool": tool_name,
                    "asset_path": asset_path,
                    "reviewer": reviewer,
                    "notes": notes,
                },
            )
