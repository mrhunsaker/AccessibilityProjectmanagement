"""Shared service singletons.

Import the objects from this module whenever you need a service instance.
All callers share the same in-memory state, so e.g. jobs enqueued via the
REST API are visible in the NiceGUI workflow monitor and vice-versa.
"""

from __future__ import annotations

from .analytics import AnalyticsService
from .authentication import AuthenticationService
from .provenance_registry import ProvenanceRegistry
from .workflow_queue import WorkflowQueueService

queue: WorkflowQueueService = WorkflowQueueService()
analytics: AnalyticsService = AnalyticsService()
provenance: ProvenanceRegistry = ProvenanceRegistry()
auth: AuthenticationService = AuthenticationService()

__all__ = ["queue", "analytics", "provenance", "auth"]
