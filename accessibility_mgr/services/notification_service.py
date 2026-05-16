"""Operational notification and escalation delivery."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class Notification:
    recipient: str
    channel: str
    subject: str
    message: str
    delivered_at: str


class NotificationService:
    """Notification delivery abstraction.

    Future adapters:
    - email
    - Slack
    - Teams
    - PagerDuty
    - webhooks
    """

    def __init__(self) -> None:
        self._notifications: list[Notification] = []

    def deliver(
        self,
        *,
        recipient: str,
        channel: str,
        subject: str,
        message: str,
    ) -> Notification:
        notification = Notification(
            recipient=recipient,
            channel=channel,
            subject=subject,
            message=message,
            delivered_at=datetime.now(timezone.utc).isoformat(),
        )

        self._notifications.append(notification)
        return notification

    def notify_sla_breach(
        self,
        *,
        workflow_name: str,
        asset_id: int,
        recipient: str,
    ) -> Notification:
        return self.deliver(
            recipient=recipient,
            channel="operations",
            subject="SLA Breach Detected",
            message=(
                f"Workflow '{workflow_name}' breached SLA "
                f"for asset #{asset_id}."
            ),
        )

    def list_notifications(self) -> list[dict[str, Any]]:
        return [
            asdict(notification)
            for notification in self._notifications
        ]


__all__ = [
    "NotificationService",
    "Notification",
]
