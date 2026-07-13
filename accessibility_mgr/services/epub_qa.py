"""EPUB QA automation services.

Provides orchestration primitives for automated EPUB accessibility
quality assurance workflows and pipeline execution tracking.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .toolchain_binaries import AccessibilityBinaryIntegrationService


@dataclass(slots=True)
class QAIssue:
    severity: str
    code: str
    message: str
    location: str | None = None


@dataclass(slots=True)
class QAResult:
    passed: bool
    score: int
    engine: str
    checked_at: str
    issues: list[QAIssue] = field(default_factory=list)


@dataclass(slots=True)
class PipelineRun:
    pipeline_name: str
    asset_id: int
    status: str
    started_at: str
    completed_at: str | None = None
    retry_count: int = 0
    logs: list[str] = field(default_factory=list)


class EPUBQAService:
    """Accessibility QA orchestration service."""

    def __init__(
        self,
        binary_service: AccessibilityBinaryIntegrationService | None = None,
    ) -> None:
        self._runs: list[PipelineRun] = []
        self._reports: dict[int, QAResult] = {}
        self.binary_service = binary_service or AccessibilityBinaryIntegrationService()

    def start_pipeline(
        self,
        *,
        pipeline_name: str,
        asset_id: int,
    ) -> PipelineRun:
        run = PipelineRun(
            pipeline_name=pipeline_name,
            asset_id=asset_id,
            status="running",
            started_at=datetime.now(timezone.utc).isoformat(),
        )

        self._runs.append(run)
        return run

    def append_log(
        self,
        run: PipelineRun,
        message: str,
    ) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        run.logs.append(f"{timestamp} {message}")

    def complete_pipeline(
        self,
        run: PipelineRun,
        *,
        success: bool,
    ) -> None:
        run.status = "completed" if success else "failed"
        run.completed_at = datetime.now(timezone.utc).isoformat()

    def retry_pipeline(self, run: PipelineRun) -> None:
        run.retry_count += 1
        run.status = "retrying"
        self.append_log(run, "Pipeline retry requested")

    def run_ace_check(
        self,
        *,
        asset_id: int,
        epub_path: str,
    ) -> QAResult:
        """Run a real DAISY Ace accessibility audit against *epub_path*.

        AUDIT-FIX-002: this previously fabricated a score from the file
        extension and the word "draft" in the filename and never invoked
        Ace at all. It now calls AccessibilityBinaryIntegrationService,
        which runs the real `ace` CLI, and parses the JSON report Ace
        writes to its output directory. If Ace is not installed, or the
        report can't be parsed, that is reported honestly — the result is
        never silently marked as passed.
        """

        path = Path(epub_path)
        issues: list[QAIssue] = []

        if path.suffix.lower() != ".epub":
            issues.append(
                QAIssue(
                    severity="error",
                    code="INVALID_FORMAT",
                    message="Input file is not an EPUB package",
                )
            )
            result = QAResult(
                passed=False,
                score=0,
                engine="DAISY Ace",
                checked_at=datetime.now(timezone.utc).isoformat(),
                issues=issues,
            )
            self._reports[asset_id] = result
            return result

        if not path.exists():
            issues.append(
                QAIssue(
                    severity="error",
                    code="FILE_NOT_FOUND",
                    message=f"EPUB file not found: {epub_path}",
                )
            )
            result = QAResult(
                passed=False,
                score=0,
                engine="DAISY Ace",
                checked_at=datetime.now(timezone.utc).isoformat(),
                issues=issues,
            )
            self._reports[asset_id] = result
            return result

        outcome = self.binary_service.run_daisy_ace(epub_path)

        if outcome.get("status") == "unavailable":
            issues.append(
                QAIssue(
                    severity="error",
                    code="TOOL_UNAVAILABLE",
                    message=outcome.get(
                        "reason", "DAISY Ace CLI is not installed"
                    ),
                )
            )
            result = QAResult(
                passed=False,
                score=0,
                engine="DAISY Ace (unavailable)",
                checked_at=datetime.now(timezone.utc).isoformat(),
                issues=issues,
            )
            self._reports[asset_id] = result
            return result

        execution = outcome.get("execution", {})
        exit_code = execution.get("exit_code", 1)
        output_dir = outcome.get("output_directory")
        report_issues, report_parsed = self._parse_ace_report(output_dir)
        issues.extend(report_issues)

        if exit_code != 0 and not report_parsed:
            # Ace ran and reported failure, and we have no structured
            # report to explain why — surface the raw stderr instead of
            # guessing.
            stderr = (execution.get("stderr") or "").strip()
            issues.append(
                QAIssue(
                    severity="error",
                    code="ACE_EXECUTION_FAILED",
                    message=stderr[:500] if stderr else (
                        f"DAISY Ace exited with code {exit_code}"
                    ),
                )
            )

        error_count = sum(1 for i in issues if i.severity == "error")
        warning_count = sum(1 for i in issues if i.severity == "warning")
        score = max(0, 100 - (error_count * 15) - (warning_count * 5))

        result = QAResult(
            passed=exit_code == 0 and error_count == 0,
            score=score,
            engine="DAISY Ace",
            checked_at=datetime.now(timezone.utc).isoformat(),
            issues=issues,
        )

        self._reports[asset_id] = result
        return result

    @staticmethod
    def _parse_ace_report(
        output_dir: str | None,
    ) -> tuple[list[QAIssue], bool]:
        """Best-effort parse of Ace's report.json.

        Ace's report schema has changed across versions, so this looks for
        the most common shapes (an 'assertions'/'violations' list with
        'severity' or 'earl:result' entries) rather than assuming one exact
        structure. Returns (issues, parsed_successfully).
        """
        if not output_dir:
            return [], False

        report_path = Path(output_dir) / "report.json"
        if not report_path.exists():
            return [], False

        try:
            data = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return [], False

        raw_entries: list[dict[str, Any]] = []
        for key in ("assertions", "violations", "issues"):
            value = data.get(key) if isinstance(data, dict) else None
            if isinstance(value, list):
                raw_entries = value
                break

        issues: list[QAIssue] = []
        for entry in raw_entries:
            if not isinstance(entry, dict):
                continue

            earl_result = entry.get("earl:result")
            if entry.get("severity"):
                severity = str(entry["severity"])
            elif isinstance(earl_result, dict) and earl_result.get("earl:outcome"):
                severity = str(earl_result["earl:outcome"])
            else:
                severity = "warning"
            severity = severity.lower()
            if severity not in {"error", "warning", "info"}:
                severity = "warning"

            issues.append(
                QAIssue(
                    severity=severity,
                    code=str(entry.get("code") or entry.get("rule") or "ACE_RULE"),
                    message=str(
                        entry.get("message")
                        or entry.get("description")
                        or "Accessibility rule violation reported by Ace"
                    ),
                    location=str(entry.get("location"))
                    if entry.get("location")
                    else None,
                )
            )

        return issues, True

    def get_report(self, asset_id: int) -> QAResult | None:
        return self._reports.get(asset_id)

    def list_pipeline_runs(self) -> list[dict[str, Any]]:
        return [
            {
                "pipeline_name": run.pipeline_name,
                "asset_id": run.asset_id,
                "status": run.status,
                "started_at": run.started_at,
                "completed_at": run.completed_at,
                "retry_count": run.retry_count,
                "logs": run.logs,
            }
            for run in self._runs
        ]


__all__ = [
    "EPUBQAService",
    "PipelineRun",
    "QAIssue",
    "QAResult",
]
