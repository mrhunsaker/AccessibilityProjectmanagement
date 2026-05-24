"""Event streaming and webhook infrastructure."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class EventSubscription:
    event_type: str
    callback_url: str
    active: bool


@dataclass(slots=True)
class PlatformEvent:
    event_type: str
    payload: dict[str, Any]
    created_at: str


class EventStreamService:
    """Internal event stream abstraction.

    Future targets:
    - webhook delivery
    - Kafka/NATS adapters
    - distributed event streaming
    - audit event propagation
    """

    def __init__(self) -> None:
        self._subscriptions: list[EventSubscription] = []
        self._events: list[PlatformEvent] = []

    def subscribe(
        self,
        *,
        event_type: str,
        callback_url: str,
    ) -> None:
        self._subscriptions.append(
            EventSubscription(
                event_type=event_type,
                callback_url=callback_url,
                active=True,
            )
        )

    def publish(
        self,
        *,
        event_type: str,
        payload: dict[str, Any],
    ) -> PlatformEvent:
        event = PlatformEvent(
            event_type=event_type,
            payload=payload,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        self._events.append(event)
        return event

    def list_events(self) -> list[dict[str, Any]]:
        return [asdict(event) for event in self._events]

    def list_subscriptions(self) -> list[dict[str, Any]]:
        return [
            {
                "event_type": subscription.event_type,
                "callback_url": subscription.callback_url,
                "active": subscription.active,
            }
            for subscription in self._subscriptions
        ]


__all__ = [
    "EventStreamService",
    "EventSubscription",
    "PlatformEvent",
]
