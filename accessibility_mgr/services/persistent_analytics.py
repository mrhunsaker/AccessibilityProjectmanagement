"""Persistent analytics compatibility service.

This module provides the class name expected by the REST layer while
reusing the existing in-memory analytics implementation.
"""

from __future__ import annotations

from .analytics import AnalyticsService


class PersistentAnalyticsService(AnalyticsService):
    """Compatibility wrapper for API-facing analytics access."""


__all__ = [
    "PersistentAnalyticsService",
]
