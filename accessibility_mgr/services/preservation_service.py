"""
Preservation service — fixity generation and PREMIS event recording.

generate_checksum() computes SHA-256 for any file path.
record_premis_event() persists events to the metadata_event table via
db.queries.log_event(), which is the single authoritative PREMIS record.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Optional

from ..db import queries as Q


class PreservationService:
    """Service for fixity checks and PREMIS event persistence."""

    @staticmethod
    def generate_checksum(path: str) -> str:
        """Compute and return the SHA-256 hex digest of the file at *path*."""
        file_path = Path(path)
        if not file_path.exists():
            return "missing"
        h = hashlib.sha256()
        with open(file_path, "rb") as handle:
            while chunk := handle.read(65536):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def verify_checksum(path: str, expected: str) -> bool:
        """Return True if the file's current SHA-256 matches *expected*."""
        return PreservationService.generate_checksum(path) == expected

    @staticmethod
    def record_premis_event(
        job_type: str,
        job_id: int,
        event_type: str,
        event_outcome: str = "SUCCESS",
        agent: str = "system",
        detail: str = "",
        step_key: Optional[str] = None,
        file_object_id: Optional[int] = None,
        extra_metadata: Optional[dict[str, Any]] = None,
    ) -> int:
        """Persist a PREMIS-style event to the metadata_event table and return its id."""
        return Q.log_event(
            job_type=job_type,
            job_id=job_id,
            event_type=event_type,
            event_outcome=event_outcome,
            step_key=step_key,
            file_object_id=file_object_id,
            agent=agent,
            detail=detail,
            extra_metadata=extra_metadata,
        )

    @staticmethod
    def ingest_and_record(
        source_path: str,
        job_type: str,
        job_id: int,
        file_use: str = "ORIGINAL",
        format_name: str = "",
        step_key: Optional[str] = None,
        agent: str = "system",
    ) -> int:
        """
        Ingest a file into the file store, link it to a job, and record a PREMIS
        INGEST event.  Returns the file_object id.
        """
        file_id = Q.ingest_file(
            source_path=source_path,
            file_use=file_use,
            format_name=format_name,
        )
        Q.link_file_to_job(file_id, job_type, job_id, step_key=step_key)
        from pathlib import Path as _Path
        Q.log_event(
            job_type=job_type,
            job_id=job_id,
            event_type="INGEST",
            event_outcome="SUCCESS",
            step_key=step_key,
            file_object_id=file_id,
            agent=agent,
            detail=f"Ingested {_Path(source_path).name} as {file_use}",
        )
        return file_id
