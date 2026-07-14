"""SLA monitoring and operational escalation infrastructure — SQLite-backed."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


def _default_db_path() -> Path:
    try:
        from ..db.schema import DB_PATH
        return DB_PATH
    except Exception:
        return Path("accessibility_mgr.db")


class SLAMonitoringService:
    """SQLite-backed SLA and escalation monitoring."""

    def __init__(self, database_path: Path | None = None) -> None:
        self.database_path = database_path or _default_db_path()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS sla_record (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_name TEXT NOT NULL,
                    asset_id INTEGER NOT NULL,
                    started_at TEXT NOT NULL,
                    sla_minutes INTEGER NOT NULL DEFAULT 30,
                    breached INTEGER NOT NULL DEFAULT 0
                )"""
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS escalation_event (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_name TEXT NOT NULL,
                    asset_id INTEGER NOT NULL,
                    severity TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )"""
            )

    def register_workflow(
        self,
        *,
        workflow_name: str,
        asset_id: int,
        sla_minutes: int = 30,
    ) -> dict[str, Any]:
        started_at = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO sla_record (workflow_name, asset_id, started_at, sla_minutes, breached) "
                "VALUES (?, ?, ?, ?, 0)",
                (workflow_name, asset_id, started_at, sla_minutes),
            )
        return {
            "workflow_name": workflow_name,
            "asset_id": asset_id,
            "started_at": started_at,
            "sla_minutes": sla_minutes,
            "breached": False,
        }

    def evaluate_slas(self) -> list[dict[str, Any]]:
        now = datetime.now(UTC)
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM sla_record").fetchall()
            for row in rows:
                started = datetime.fromisoformat(row["started_at"])
                deadline = started + timedelta(minutes=row["sla_minutes"])
                if now > deadline and not row["breached"]:
                    conn.execute(
                        "UPDATE sla_record SET breached = 1 WHERE id = ?", (row["id"],)
                    )
                    conn.execute(
                        "INSERT INTO escalation_event (workflow_name, asset_id, severity, summary, created_at) "
                        "VALUES (?, ?, 'high', 'Workflow SLA breached', ?)",
                        (row["workflow_name"], row["asset_id"], now.isoformat()),
                    )
            return [
                {
                    "workflow_name": r["workflow_name"],
                    "asset_id": r["asset_id"],
                    "started_at": r["started_at"],
                    "sla_minutes": r["sla_minutes"],
                    "breached": bool(r["breached"]),
                }
                for r in conn.execute("SELECT * FROM sla_record").fetchall()
            ]

    def list_escalations(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            return [
                {
                    "workflow_name": r["workflow_name"],
                    "asset_id": r["asset_id"],
                    "severity": r["severity"],
                    "summary": r["summary"],
                    "created_at": r["created_at"],
                }
                for r in conn.execute(
                    "SELECT * FROM escalation_event ORDER BY id"
                ).fetchall()
            ]

    def health_summary(self) -> dict[str, Any]:
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM sla_record").fetchone()[0]
            breached = conn.execute(
                "SELECT COUNT(*) FROM sla_record WHERE breached = 1"
            ).fetchone()[0]
            escalations = conn.execute("SELECT COUNT(*) FROM escalation_event").fetchone()[0]
            return {
                "tracked_workflows": total,
                "sla_breaches": breached,
                "healthy_workflows": total - breached,
                "escalations": escalations,
            }


__all__ = ["SLAMonitoringService"]
