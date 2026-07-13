"""CI/CD accessibility validation hook infrastructure."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any

from ..db import queries as Q
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
    """CI/CD accessibility validation orchestration service.

    AUDIT-FIX (follow-up): validation runs are now persisted via
    db.queries.log_cicd_validation_run() so history survives an app
    restart and is visible from both the REST API and the UI, instead of
    living only in a private in-memory list that was wiped on restart.
    """

    def __init__(self) -> None:
        self.binary_service = AccessibilityBinaryIntegrationService()

    def validate_epub_pipeline(
        self,
        *,
        pipeline_id: str,
        epub_path: str,
    ) -> PipelineValidationResult:
        ace_result = self.binary_service.run_daisy_ace(epub_path)
        epubcheck_result = self.binary_service.run_epubcheck(epub_path)

        ace_unavailable = ace_result.get("status") == "unavailable"
        epubcheck_unavailable = epubcheck_result.get("status") == "unavailable"

        ace_exit_code = ace_result.get("execution", {}).get("exit_code")
        epubcheck_exit_code = epubcheck_result.get("execution", {}).get("exit_code")

        if ace_unavailable or epubcheck_unavailable:
            # Can't validate accessibility if a tool isn't installed on the
            # CI runner — this must not be reported as a pass.
            status = "warning"
        elif ace_exit_code != 0 or epubcheck_exit_code != 0:
            # AUDIT-FIX-003: previously there was no branch for this case at
            # all, so a non-zero exit code (real accessibility / EPUB
            # validation violations) was silently reported as "passed" as
            # long as both binaries were installed. A release-blocking gate
            # must fail here.
            status = "failed"
        else:
            status = "passed"

        executed_at = datetime.now(timezone.utc).isoformat()

        result = PipelineValidationResult(
            pipeline_id=pipeline_id,
            workflow_name="epub-accessibility-validation",
            status=status,
            executed_at=executed_at,
            metadata={
                "ace": ace_result,
                "epubcheck": epubcheck_result,
            },
        )

        Q.log_cicd_validation_run(
            pipeline_id=pipeline_id,
            epub_path=epub_path,
            status=status,
            executed_at=executed_at,
            ace_exit=ace_exit_code,
            epubcheck_exit=epubcheck_exit_code,
        )

        return result

    def list_history(self) -> list[dict]:
        return Q.list_cicd_validation_runs(limit=50)


__all__ = [
    "PipelineValidationResult",
    "CICDValidationHookService",
]
