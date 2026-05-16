"""Persistent QA workflow service backed by SQLite."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .sqlite_store import SQLiteStore


class PersistentQAService:
    """Durable QA persistence and pipeline history service."""

    def __init__(self, store: SQLiteStore | None = None) -> None:
        self.store = store or SQLiteStore()

    def persist_report(
        self,
        *,
        asset_id: int,
        pipeline_name: str,
        status: str,
        score: int,
        findings: list[dict[str, Any]],
    ) -> None:
        self.store.execute(
            """
            INSERT INTO qa_report (
                asset_id,
                pipeline_name,
                status,
                score,
                findings_json,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                asset_id,
                pipeline_name,
                status,
                score,
                json.dumps(findings),
                datetime.now(timezone.utc).isoformat(),
            ),
        )

    def persist_pipeline_run(
        self,
        *,
        asset_id: int,
        pipeline_name: str,
        status: str,
        retry_count: int,
        logs: list[str],
    ) -> None:
        self.store.execute(
            """
            INSERT INTO pipeline_run (
                asset_id,
                pipeline_name,
                status,
                retry_count,
                logs_json,
                persisted_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                asset_id,
                pipeline_name,
                status,
                retry_count,
                json.dumps(logs),
                datetime.now(timezone.utc).isoformat(),
            ),
        )

    def list_reports(self) -> list[dict[str, Any]]:
        return self.store.fetch_all(
            """
            SELECT *
            FROM qa_report
            ORDER BY created_at DESC
            """
        )

    def list_pipeline_runs(self) -> list[dict[str, Any]]:
        return self.store.fetch_all(
            """
            SELECT *
            FROM pipeline_run
            ORDER BY persisted_at DESC
            """
        )


__all__ = ["PersistentQAService"]
