"""Compliance reporting and signed provenance exports."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any

from .audit_log import AuditLogService
from .persistent_provenance import PersistentProvenanceRegistry


@dataclass(slots=True)
class ComplianceExport:
    export_type: str
    generated_at: str
    signature: str
    payload: dict[str, Any]


class ComplianceReportingService:
    """Governance and compliance export service."""

    def __init__(self) -> None:
        self.audit_log = AuditLogService()
        self.provenance = PersistentProvenanceRegistry()

    def generate_provenance_export(self) -> dict[str, Any]:
        payload = {
            "events": self.provenance.list_events(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        signature = self._sign_payload(payload)

        export = ComplianceExport(
            export_type="provenance",
            generated_at=datetime.now(timezone.utc).isoformat(),
            signature=signature,
            payload=payload,
        )

        self.audit_log.record_event(
            event_type="compliance_export_generated",
            actor="system",
            payload={
                "export_type": "provenance",
                "signature": signature,
            },
        )

        return asdict(export)

    def generate_governance_report(self) -> dict[str, Any]:
        payload = {
            "audit_events": self.audit_log.list_events(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        signature = self._sign_payload(payload)

        export = ComplianceExport(
            export_type="governance",
            generated_at=datetime.now(timezone.utc).isoformat(),
            signature=signature,
            payload=payload,
        )

        return asdict(export)

    def _sign_payload(self, payload: dict[str, Any]) -> str:
        serialized = json.dumps(payload, sort_keys=True)

        return hashlib.sha256(
            serialized.encode("utf-8")
        ).hexdigest()


__all__ = [
    "ComplianceReportingService",
    "ComplianceExport",
]
