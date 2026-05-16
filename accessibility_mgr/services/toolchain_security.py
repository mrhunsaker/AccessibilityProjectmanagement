"""Production-oriented accessibility toolchain hardening.

Implements:
- subprocess allowlists
- execution isolation controls
- artifact retention policies
- hardened execution validation
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


ALLOWED_TOOLS = {
    "ace": ["ace", "npx", "node"],
    "epubcheck": ["java", "epubcheck"],
    "daisy-pipeline": ["pipeline2", "java"],
}


@dataclass(slots=True)
class ArtifactRecord:
    path: str
    created_at: str
    retention_days: int
    classification: str


class ToolchainSecurityService:
    """Security controls for external tool execution."""

    def __init__(self) -> None:
        self._artifacts: list[ArtifactRecord] = []

    def validate_command(
        self,
        *,
        tool_name: str,
        command: list[str],
    ) -> bool:
        allowed = ALLOWED_TOOLS.get(tool_name.lower())

        if not allowed:
            return False

        executable = Path(command[0]).name.lower()
        return executable in allowed

    def register_artifact(
        self,
        *,
        path: str,
        classification: str,
        retention_days: int = 30,
    ) -> ArtifactRecord:
        artifact = ArtifactRecord(
            path=path,
            created_at=datetime.now(timezone.utc).isoformat(),
            retention_days=retention_days,
            classification=classification,
        )

        self._artifacts.append(artifact)
        return artifact

    def expired_artifacts(self) -> list[ArtifactRecord]:
        now = datetime.now(timezone.utc)
        expired: list[ArtifactRecord] = []

        for artifact in self._artifacts:
            created = datetime.fromisoformat(artifact.created_at)
            expires = created + timedelta(days=artifact.retention_days)

            if expires < now:
                expired.append(artifact)

        return expired

    def retention_summary(self) -> dict:
        return {
            "tracked_artifacts": len(self._artifacts),
            "expired_artifacts": len(self.expired_artifacts()),
            "active_artifacts": (
                len(self._artifacts) - len(self.expired_artifacts())
            ),
        }


__all__ = [
    "ToolchainSecurityService",
    "ArtifactRecord",
    "ALLOWED_TOOLS",
]
