"""Shared service singletons.

Import the objects from this module whenever you need a service instance.
All callers share the same state, so e.g. jobs enqueued via the REST API
are visible in the NiceGUI workflow monitor and vice-versa.

AUDIT-FIX-004/006/007: queue/analytics/provenance now use the SQLite-backed
implementations (PersistentWorkflowQueue, PersistentAnalyticsService,
PersistentProvenanceRegistry) so this shared state also survives an app
restart, instead of being wiped every time the process restarts.
"""

from __future__ import annotations

from .authentication import AuthenticationService
from .persistent_analytics import PersistentAnalyticsService
from .persistent_provenance import PersistentProvenanceRegistry
from .persistent_queue import PersistentWorkflowQueue

queue: PersistentWorkflowQueue = PersistentWorkflowQueue()
analytics: PersistentAnalyticsService = PersistentAnalyticsService()
provenance: PersistentProvenanceRegistry = PersistentProvenanceRegistry()
auth: AuthenticationService = AuthenticationService()

__all__ = ["queue", "analytics", "provenance", "auth"]
