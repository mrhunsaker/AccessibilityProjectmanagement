"""Persistent analytics service backed by SQLite."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .sqlite_store import SQLiteStore


class PersistentAnalyticsService:
    """Durable KPI and analytics persistence service."""

    def __init__(self, store: SQLiteStore | None = None) -> None:
        self.store = store or SQLiteStore()

    def record_metric(
        self,
        *,
        metric_name: str,
        metric_value: float,
        category: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.store.execute(
            """
            INSERT INTO analytics_metric (
                metric_name,
                metric_value,
                category,
                metadata_json,
                recorded_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                metric_name,
                metric_value,
                category,
                json.dumps(metadata or {}),
                datetime.now(timezone.utc).isoformat(),
            ),
        )

    def list_metrics(self) -> list[dict[str, Any]]:
        return self.store.fetch_all(
            """
            SELECT *
            FROM analytics_metric
            ORDER BY recorded_at DESC
            """
        )

    def summarize(self) -> dict[str, Any]:
        metrics = self.list_metrics()

        if not metrics:
            return {
                "total_metrics": 0,
                "average_score": 0,
                "categories": {},
            }

        total = len(metrics)
        average = sum(m["metric_value"] for m in metrics) / total

        categories: dict[str, int] = {}

        for metric in metrics:
            category = metric["category"]
            categories[category] = categories.get(category, 0) + 1

        return {
            "total_metrics": total,
            "average_score": round(average, 2),
            "categories": categories,
        }


__all__ = ["PersistentAnalyticsService"]
