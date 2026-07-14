"""Persistent analytics service — SQLite-backed KPI storage.

AUDIT-FIX-007: this was previously an empty subclass of AnalyticsService
with no override at all:

    class PersistentAnalyticsService(AnalyticsService):
        '''Compatibility wrapper for API-facing analytics access.'''

Despite the name, every metric was stored in a plain Python list and lost
on every restart. This now persists metrics to a real SQLite table in the
same database the rest of the application uses.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .analytics import AnalyticsService, KPIRecord


def _default_db_path() -> Path:
    try:
        from ..db.schema import DB_PATH
        return DB_PATH
    except Exception:
        # Fallback for standalone / test use where schema is not importable
        return Path("accessibility_mgr.db")


class PersistentAnalyticsService(AnalyticsService):
    """SQLite-backed analytics service."""

    def __init__(self, database_path: Path | None = None) -> None:
        super().__init__()
        self.database_path = database_path or _default_db_path()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self.database_path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS analytics_metric (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    category TEXT NOT NULL,
                    recorded_at TEXT NOT NULL,
                    metadata TEXT
                )
                """
            )

    def record_metric(
        self,
        *,
        metric_name: str,
        metric_value: float,
        category: str,
        metadata: dict[str, Any] | None = None,
    ) -> KPIRecord:
        record = KPIRecord(
            metric_name=metric_name,
            metric_value=metric_value,
            category=category,
            recorded_at=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {},
        )

        with self._connect() as connection:
            connection.execute(
                "INSERT INTO analytics_metric "
                "(metric_name, metric_value, category, recorded_at, metadata) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    record.metric_name,
                    record.metric_value,
                    record.category,
                    record.recorded_at,
                    json.dumps(record.metadata),
                ),
            )

        return record

    def summarize(self) -> dict[str, Any]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT metric_value, category FROM analytics_metric"
            ).fetchall()

        total = len(rows)
        if not total:
            return {"total_metrics": 0, "average_score": 0, "categories": {}}

        avg = sum(value for value, _ in rows) / total

        categories: dict[str, int] = {}
        for _, category in rows:
            categories[category] = categories.get(category, 0) + 1

        return {
            "total_metrics": total,
            "average_score": round(avg, 2),
            "categories": categories,
        }

    def list_metrics(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT metric_name, metric_value, category, recorded_at, metadata "
                "FROM analytics_metric ORDER BY id DESC"
            ).fetchall()

        results = []
        for name, value, category, recorded_at, metadata in rows:
            results.append(
                {
                    "metric_name": name,
                    "metric_value": value,
                    "category": category,
                    "recorded_at": recorded_at,
                    "metadata": json.loads(metadata) if metadata else {},
                }
            )
        return results


__all__ = [
    "PersistentAnalyticsService",
]
