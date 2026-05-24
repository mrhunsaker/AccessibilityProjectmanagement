"""Audit-grade operational event logging."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class AuditEvent:
    event_type: str
    actor: str
    payload: dict[str, Any]
    event_hash: str
    created_at: str


class AuditLogService:
    """Immutable-style audit event logging service."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def record_event(
        self,
        *,
        event_type: str,
        actor: str,
        payload: dict[str, Any],
    ) -> AuditEvent:
        created_at = datetime.now(timezone.utc).isoformat()

        digest_payload = json.dumps(
            {
                "event_type": event_type,
                "actor": actor,
                "payload": payload,
                "created_at": created_at,
            },
            sort_keys=True,
        )

        event_hash = hashlib.sha256(
            digest_payload.encode("utf-8")
        ).hexdigest()

        event = AuditEvent(
            event_type=event_type,
            actor=actor,
            payload=payload,
            event_hash=event_hash,
            created_at=created_at,
        )

        self._events.append(event)
        return event

    def list_events(self) -> list[dict[str, Any]]:
        return [asdict(event) for event in self._events]

    def verify_integrity(self) -> bool:
        for event in self._events:
            digest_payload = json.dumps(
                {
                    "event_type": event.event_type,
                    "actor": event.actor,
                    "payload": event.payload,
                    "created_at": event.created_at,
                },
                sort_keys=True,
            )

            calculated = hashlib.sha256(
                digest_payload.encode("utf-8")
            ).hexdigest()

            if calculated != event.event_hash:
                return False

        return True


__all__ = [
    "AuditLogService",
    "AuditEvent",
]
