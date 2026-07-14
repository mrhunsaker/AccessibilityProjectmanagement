"""Audit-grade operational event logging — SQLite-backed."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _default_db_path() -> Path:
    try:
        from ..db.schema import DB_PATH
        return DB_PATH
    except Exception:
        return Path("accessibility_mgr.db")


class AuditLogService:
    """SQLite-backed immutable-style audit event logging service."""

    def __init__(self, database_path: Path | None = None) -> None:
        self.database_path = database_path or _default_db_path()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS audit_event (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    payload_json TEXT NOT NULL DEFAULT '{}',
                    event_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )"""
            )

    def record_event(
        self,
        *,
        event_type: str,
        actor: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        created_at = datetime.now(UTC).isoformat()
        payload_json = json.dumps(payload, sort_keys=True)

        digest_payload = json.dumps(
            {"event_type": event_type, "actor": actor, "payload": payload, "created_at": created_at},
            sort_keys=True,
        )
        event_hash = hashlib.sha256(digest_payload.encode("utf-8")).hexdigest()

        with self._connect() as conn:
            conn.execute(
                "INSERT INTO audit_event (event_type, actor, payload_json, event_hash, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (event_type, actor, payload_json, event_hash, created_at),
            )

        return {
            "event_type": event_type,
            "actor": actor,
            "payload": payload,
            "event_hash": event_hash,
            "created_at": created_at,
        }

    def list_events(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            return [
                {
                    "event_type": r["event_type"],
                    "actor": r["actor"],
                    "payload": json.loads(r["payload_json"]),
                    "event_hash": r["event_hash"],
                    "created_at": r["created_at"],
                }
                for r in conn.execute("SELECT * FROM audit_event ORDER BY id").fetchall()
            ]

    def verify_integrity(self) -> bool:
        with self._connect() as conn:
            for event in conn.execute("SELECT * FROM audit_event ORDER BY id").fetchall():
                payload = json.loads(event["payload_json"])
                digest_payload = json.dumps(
                    {"event_type": event["event_type"], "actor": event["actor"],
                     "payload": payload, "created_at": event["created_at"]},
                    sort_keys=True,
                )
                calculated = hashlib.sha256(digest_payload.encode("utf-8")).hexdigest()
                if calculated != event["event_hash"]:
                    return False
            return True


__all__ = ["AuditLogService"]
