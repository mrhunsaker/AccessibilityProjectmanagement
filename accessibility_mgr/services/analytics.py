"""Operational analytics and KPI aggregation services."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class KPIRecord:
    metric_name: str
    metric_value: float
    category: str
    recorded_at: str
    metadata: dict[str, Any]


class AnalyticsService:
    """Aggregates operational QA and production KPIs."""

    def __init__(self) -> None:
        self._records: list[KPIRecord] = []

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

        self._records.append(record)
        return record

    def summarize(self) -> dict[str, Any]:
        total = len(self._records)

        if not total:
            return {
                "total_metrics": 0,
                "average_score": 0,
                "categories": {},
            }

        avg = sum(r.metric_value for r in self._records) / total

        categories: dict[str, int] = {}

        for record in self._records:
            categories[record.category] = (
                categories.get(record.category, 0) + 1
            )

        return {
            "total_metrics": total,
            "average_score": round(avg, 2),
            "categories": categories,
        }

    def list_metrics(self) -> list[dict[str, Any]]:
        return [asdict(record) for record in self._records]


__all__ = [
    "AnalyticsService",
    "KPIRecord",
]
