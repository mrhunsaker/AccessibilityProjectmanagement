"""Unified provenance registry.

Aggregates metadata audit events, QA artifacts, and QA execution
history into a normalized provenance timeline abstraction.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class ProvenanceEvent:
    asset_id: int
    event_type: str
    summary: str
    created_at: str
    metadata: dict[str, Any]


class ProvenanceRegistry:
    """Central provenance aggregation service."""

    def __init__(self) -> None:
        self._events: list[ProvenanceEvent] = []

    def register_event(
        self,
        *,
        asset_id: int,
        event_type: str,
        summary: str,
        metadata: dict[str, Any] | None = None,
    ) -> ProvenanceEvent:
        event = ProvenanceEvent(
            asset_id=asset_id,
            event_type=event_type,
            summary=summary,
            created_at=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {},
        )

        self._events.append(event)
        return event

    def list_events(
        self,
        *,
        asset_id: int | None = None,
    ) -> list[dict[str, Any]]:
        events = self._events

        if asset_id is not None:
            events = [
                event for event in events
                if event.asset_id == asset_id
            ]

        return [asdict(event) for event in events]


__all__ = [
    "ProvenanceEvent",
    "ProvenanceRegistry",
]
