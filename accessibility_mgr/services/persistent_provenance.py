"""Persistent provenance compatibility service.

This module provides the class name expected by API and compliance layers
while reusing the existing provenance registry implementation.
"""

from __future__ import annotations

from .provenance_registry import ProvenanceRegistry


class PersistentProvenanceRegistry(ProvenanceRegistry):
    """Compatibility wrapper for API-facing provenance access."""


__all__ = [
    "PersistentProvenanceRegistry",
]
