"""SLA monitoring and operational escalation infrastructure."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from typing import Any


@dataclass(slots=True)
class SLARecord:
    workflow_name: str
    asset_id: int
    started_at: str
    sla_minutes: int
    breached: bool


@dataclass(slots=True)
class EscalationEvent:
    workflow_name: str
    asset_id: int
    severity: str
    summary: str
    created_at: str


class SLAMonitoringService:
    """Operational SLA and escalation monitoring."""

    def __init__(self) -> None:
        self._records: list[SLARecord] = []
        self._escalations: list[EscalationEvent] = []

    def register_workflow(
        self,
        *,
        workflow_name: str,
        asset_id: int,
        sla_minutes: int = 30,
    ) -> SLARecord:
        record = SLARecord(
            workflow_name=workflow_name,
            asset_id=asset_id,
            started_at=datetime.now(timezone.utc).isoformat(),
            sla_minutes=sla_minutes,
            breached=False,
        )

        self._records.append(record)
        return record

    def evaluate_slas(self) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)

        for record in self._records:
            started = datetime.fromisoformat(record.started_at)
            deadline = started + timedelta(minutes=record.sla_minutes)

            if now > deadline and not record.breached:
                record.breached = True

                self._escalations.append(
                    EscalationEvent(
                        workflow_name=record.workflow_name,
                        asset_id=record.asset_id,
                        severity="high",
                        summary="Workflow SLA breached",
                        created_at=now.isoformat(),
                    )
                )

        return [asdict(record) for record in self._records]

    def list_escalations(self) -> list[dict[str, Any]]:
        return [
            asdict(escalation)
            for escalation in self._escalations
        ]

    def health_summary(self) -> dict[str, Any]:
        breached = len([
            record for record in self._records
            if record.breached
        ])

        return {
            "tracked_workflows": len(self._records),
            "sla_breaches": breached,
            "healthy_workflows": (
                len(self._records) - breached
            ),
            "escalations": len(self._escalations),
        }


__all__ = [
    "SLAMonitoringService",
    "SLARecord",
    "EscalationEvent",
]
