"""Compliance reporting and signed provenance exports."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
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
    signature_algorithm: str
    payload: dict[str, Any]


class ComplianceReportingService:
    """Governance and compliance export service.

    AUDIT-FIX-005: exports are now signed with HMAC-SHA256 using a
    server-held key (ACCESSMAN_SIGNING_KEY) when one is configured, which
    proves both integrity and that the export was produced by a holder of
    that key. Previously this used a bare SHA-256 hash of the payload —
    that only detects accidental corruption; anyone can recompute the same
    hash for fabricated data, so it provided no real authenticity
    guarantee despite being called a "signature".

    If no signing key is configured, exports fall back to a SHA-256
    checksum and are labeled "SHA256-CHECKSUM-UNSIGNED" rather than
    silently claiming to be signed.
    """

    def __init__(self) -> None:
        self.audit_log = AuditLogService()
        self.provenance = PersistentProvenanceRegistry()
        signing_key = os.getenv("ACCESSMAN_SIGNING_KEY", "").strip()
        self._signing_key: bytes | None = (
            signing_key.encode("utf-8") if signing_key else None
        )

    def generate_provenance_export(self) -> dict[str, Any]:
        payload = {
            "events": self.provenance.list_events(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        signature, algorithm = self._sign_payload(payload)

        export = ComplianceExport(
            export_type="provenance",
            generated_at=datetime.now(timezone.utc).isoformat(),
            signature=signature,
            signature_algorithm=algorithm,
            payload=payload,
        )

        self.audit_log.record_event(
            event_type="compliance_export_generated",
            actor="system",
            payload={
                "export_type": "provenance",
                "signature": signature,
                "signature_algorithm": algorithm,
            },
        )

        return asdict(export)

    def generate_governance_report(self) -> dict[str, Any]:
        payload = {
            "audit_events": self.audit_log.list_events(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        signature, algorithm = self._sign_payload(payload)

        export = ComplianceExport(
            export_type="governance",
            generated_at=datetime.now(timezone.utc).isoformat(),
            signature=signature,
            signature_algorithm=algorithm,
            payload=payload,
        )

        return asdict(export)

    def verify_signature(
        self,
        payload: dict[str, Any],
        signature: str,
        *,
        algorithm: str,
    ) -> bool:
        """Re-derive a signature for *payload* and compare it to *signature*.

        Only meaningful for algorithm == "HMAC-SHA256" — a checksum
        ("SHA256-CHECKSUM-UNSIGNED") can be reproduced by anyone and
        verifying it proves nothing about who generated the export.
        """
        expected_signature, expected_algorithm = self._sign_payload(payload)
        if algorithm != expected_algorithm:
            return False
        return hmac.compare_digest(signature, expected_signature)

    def _sign_payload(self, payload: dict[str, Any]) -> tuple[str, str]:
        serialized = json.dumps(payload, sort_keys=True).encode("utf-8")

        if self._signing_key:
            digest = hmac.new(
                self._signing_key, serialized, hashlib.sha256
            ).hexdigest()
            return digest, "HMAC-SHA256"

        # No ACCESSMAN_SIGNING_KEY configured: fall back to an
        # integrity-only checksum and label it honestly rather than
        # calling it a signature.
        digest = hashlib.sha256(serialized).hexdigest()
        return digest, "SHA256-CHECKSUM-UNSIGNED"


__all__ = [
    "ComplianceReportingService",
    "ComplianceExport",
]
