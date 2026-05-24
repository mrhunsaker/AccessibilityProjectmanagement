"""Webhook and operational event streaming infrastructure."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class EventMessage:
    event_type: str
    payload: dict[str, Any]
    emitted_at: str


class EventStreamService:
    """Operational event streaming abstraction."""

    def __init__(self) -> None:
        self._events: list[EventMessage] = []
        self._subscribers: list[str] = []

    def subscribe(self, webhook_url: str) -> None:
        self._subscribers.append(webhook_url)

    def emit(
        self,
        *,
        event_type: str,
        payload: dict[str, Any],
    ) -> EventMessage:
        event = EventMessage(
            event_type=event_type,
            payload=payload,
            emitted_at=datetime.now(timezone.utc).isoformat(),
        )

        self._events.append(event)
        return event

    def list_events(self) -> list[dict[str, Any]]:
        return [asdict(event) for event in self._events]

    def list_subscribers(self) -> list[str]:
        return self._subscribers


__all__ = [
    "EventMessage",
    "EventStreamService",
]
