"""Metadata audit history services.

Provides append-only audit event tracking for metadata changes,
including before/after snapshots and editor attribution.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class MetadataAuditEvent:
    """Represents a metadata mutation event."""

    asset_id: int
    field_name: str
    previous_value: Any
    new_value: Any
    editor: str
    changed_at: str
    event_type: str = "metadata_update"


class MetadataAuditService:
    """In-memory audit service abstraction.

    This service intentionally avoids direct database coupling in the
    first implementation phase so it can later be connected to either:

    - SQLite persistence
    - SQLAlchemy persistence
    - external audit/event systems
    """

    def __init__(self) -> None:
        self._events: list[MetadataAuditEvent] = []

    def record_change(
        self,
        *,
        asset_id: int,
        field_name: str,
        previous_value: Any,
        new_value: Any,
        editor: str,
    ) -> MetadataAuditEvent:
        """Record a metadata mutation."""

        event = MetadataAuditEvent(
            asset_id=asset_id,
            field_name=field_name,
            previous_value=previous_value,
            new_value=new_value,
            editor=editor,
            changed_at=datetime.now(timezone.utc).isoformat(),
        )

        self._events.append(event)

        return event

    def bulk_record_changes(
        self,
        *,
        asset_id: int,
        previous_metadata: dict[str, Any],
        new_metadata: dict[str, Any],
        editor: str,
    ) -> list[MetadataAuditEvent]:
        """Record all metadata differences between two snapshots."""

        events: list[MetadataAuditEvent] = []

        all_fields = set(previous_metadata) | set(new_metadata)

        for field_name in sorted(all_fields):
            previous_value = previous_metadata.get(field_name)
            new_value = new_metadata.get(field_name)

            if previous_value == new_value:
                continue

            events.append(
                self.record_change(
                    asset_id=asset_id,
                    field_name=field_name,
                    previous_value=previous_value,
                    new_value=new_value,
                    editor=editor,
                )
            )

        return events

    def list_events(
        self,
        *,
        asset_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """Return audit events optionally filtered by asset."""

        events = self._events

        if asset_id is not None:
            events = [
                event
                for event in events
                if event.asset_id == asset_id
            ]

        return [asdict(event) for event in events]


__all__ = [
    "MetadataAuditEvent",
    "MetadataAuditService",
]
