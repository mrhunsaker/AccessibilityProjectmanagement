"""Artifact retention lifecycle management."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path


@dataclass(slots=True)
class ArtifactRecord:
    artifact_path: str
    created_at: str
    retention_days: int
    status: str


class ArtifactRetentionService:
    """Retention lifecycle management for generated artifacts."""

    def __init__(self) -> None:
        self._artifacts: list[ArtifactRecord] = []

    def register_artifact(
        self,
        artifact_path: str,
        *,
        retention_days: int = 30,
    ) -> ArtifactRecord:
        record = ArtifactRecord(
            artifact_path=artifact_path,
            created_at=datetime.now(timezone.utc).isoformat(),
            retention_days=retention_days,
            status="active",
        )

        self._artifacts.append(record)
        return record

    def evaluate_retention(self) -> list[dict]:
        now = datetime.now(timezone.utc)

        for artifact in self._artifacts:
            created = datetime.fromisoformat(artifact.created_at)
            expiry = created + timedelta(days=artifact.retention_days)

            if artifact.status == "active" and now > expiry:
                artifact.status = "expired"

        return [asdict(artifact) for artifact in self._artifacts]

    def cleanup_expired(self) -> list[str]:
        removed: list[str] = []

        for artifact in self._artifacts:
            if artifact.status != "expired":
                continue

            path = Path(artifact.artifact_path)

            if path.exists():
                path.unlink()

            removed.append(artifact.artifact_path)
            artifact.status = "deleted"

        return removed


__all__ = [
    "ArtifactRetentionService",
    "ArtifactRecord",
]
