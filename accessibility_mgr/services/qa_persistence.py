"""QA persistence and artifact tracking services.

Provides lightweight persistence abstractions for QA reports,
pipeline execution history, and generated QA artifacts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class QAArtifact:
    asset_id: int
    artifact_type: str
    file_name: str
    generated_at: str
    generated_by: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PersistedQAReport:
    asset_id: int
    pipeline_name: str
    status: str
    score: int
    created_at: str
    findings: list[dict[str, Any]] = field(default_factory=list)


class QAPersistenceService:
    """Persistence abstraction for QA workflows."""

    def __init__(self) -> None:
        self._reports: list[PersistedQAReport] = []
        self._artifacts: list[QAArtifact] = []
        self._pipeline_history: list[dict[str, Any]] = []

    def persist_report(
        self,
        *,
        asset_id: int,
        pipeline_name: str,
        status: str,
        score: int,
        findings: list[dict[str, Any]],
    ) -> PersistedQAReport:
        report = PersistedQAReport(
            asset_id=asset_id,
            pipeline_name=pipeline_name,
            status=status,
            score=score,
            created_at=datetime.now(timezone.utc).isoformat(),
            findings=findings,
        )

        self._reports.append(report)
        return report

    def persist_pipeline_run(
        self,
        *,
        pipeline_name: str,
        asset_id: int,
        status: str,
        logs: list[str],
        retry_count: int,
    ) -> dict[str, Any]:
        record = {
            "pipeline_name": pipeline_name,
            "asset_id": asset_id,
            "status": status,
            "logs": logs,
            "retry_count": retry_count,
            "persisted_at": datetime.now(timezone.utc).isoformat(),
        }

        self._pipeline_history.append(record)
        return record

    def register_artifact(
        self,
        *,
        asset_id: int,
        artifact_type: str,
        file_name: str,
        generated_by: str,
        metadata: dict[str, Any] | None = None,
    ) -> QAArtifact:
        artifact = QAArtifact(
            asset_id=asset_id,
            artifact_type=artifact_type,
            file_name=file_name,
            generated_by=generated_by,
            generated_at=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {},
        )

        self._artifacts.append(artifact)
        return artifact

    def list_reports(self) -> list[dict[str, Any]]:
        return [asdict(report) for report in self._reports]

    def list_artifacts(self) -> list[dict[str, Any]]:
        return [asdict(artifact) for artifact in self._artifacts]

    def list_pipeline_history(self) -> list[dict[str, Any]]:
        return list(self._pipeline_history)


__all__ = [
    "QAArtifact",
    "PersistedQAReport",
    "QAPersistenceService",
]
