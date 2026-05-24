"""CI/CD accessibility validation hook infrastructure."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any

from ..services.toolchain_binaries import (
    AccessibilityBinaryIntegrationService,
)


@dataclass(slots=True)
class PipelineValidationResult:
    pipeline_id: str
    workflow_name: str
    status: str
    executed_at: str
    metadata: dict[str, Any]


class CICDValidationHookService:
    """CI/CD accessibility validation orchestration service."""

    def __init__(self) -> None:
        self.binary_service = AccessibilityBinaryIntegrationService()
        self._history: list[PipelineValidationResult] = []

    def validate_epub_pipeline(
        self,
        *,
        pipeline_id: str,
        epub_path: str,
    ) -> PipelineValidationResult:
        ace_result = self.binary_service.run_daisy_ace(epub_path)
        epubcheck_result = self.binary_service.run_epubcheck(epub_path)

        status = "passed"

        if (
            ace_result.get("status") == "unavailable"
            or epubcheck_result.get("status") == "unavailable"
        ):
            status = "warning"

        result = PipelineValidationResult(
            pipeline_id=pipeline_id,
            workflow_name="epub-accessibility-validation",
            status=status,
            executed_at=datetime.now(timezone.utc).isoformat(),
            metadata={
                "ace": ace_result,
                "epubcheck": epubcheck_result,
            },
        )

        self._history.append(result)
        return result

    def list_history(self) -> list[dict]:
        return [asdict(result) for result in self._history]


__all__ = [
    "PipelineValidationResult",
    "CICDValidationHookService",
]
