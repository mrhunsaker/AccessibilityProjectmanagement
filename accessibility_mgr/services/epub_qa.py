"""EPUB QA automation services.

Provides orchestration primitives for automated EPUB accessibility
quality assurance workflows and pipeline execution tracking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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

    def __init__(self) -> None:
        self._runs: list[PipelineRun] = []
        self._reports: dict[int, QAResult] = {}

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
        """Run a simulated Ace accessibility audit.

        This implementation intentionally abstracts the actual Ace CLI
        invocation so future versions can integrate:

        - DAISY Ace
        - EPUBCheck
        - custom accessibility heuristics
        - CI/CD runners
        """

        path = Path(epub_path)

        issues: list[QAIssue] = []
        score = 100

        if not path.suffix.lower() == ".epub":
            issues.append(
                QAIssue(
                    severity="error",
                    code="INVALID_FORMAT",
                    message="Input file is not an EPUB package",
                )
            )
            score -= 50

        if "draft" in path.name.lower():
            issues.append(
                QAIssue(
                    severity="warning",
                    code="DRAFT_CONTENT",
                    message="EPUB appears to be a draft build",
                )
            )
            score -= 10

        result = QAResult(
            passed=not any(i.severity == "error" for i in issues),
            score=max(score, 0),
            engine="DAISY Ace (abstracted)",
            checked_at=datetime.now(timezone.utc).isoformat(),
            issues=issues,
        )

        self._reports[asset_id] = result
        return result

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
