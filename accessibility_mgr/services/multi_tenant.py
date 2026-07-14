"""Multi-tenant organization infrastructure — SQLite-backed."""

from __future__ import annotations

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


class MultiTenantService:
    """SQLite-backed organization and tenant isolation service."""

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
                """CREATE TABLE IF NOT EXISTS organization (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    organization_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )"""
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS tenant_membership (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    organization_id TEXT NOT NULL,
                    role TEXT NOT NULL
                )"""
            )

    def create_organization(self, name: str) -> dict[str, Any]:
        created_at = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM organization").fetchone()[0]
            org_id = f"org-{count + 1}"
            conn.execute(
                "INSERT INTO organization (organization_id, name, created_at) VALUES (?, ?, ?)",
                (org_id, name, created_at),
            )
        return {
            "organization_id": org_id,
            "name": name,
            "created_at": created_at,
        }

    def add_member(
        self,
        *,
        username: str,
        organization_id: str,
        role: str,
    ) -> dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO tenant_membership (username, organization_id, role) VALUES (?, ?, ?)",
                (username, organization_id, role),
            )
        return {
            "username": username,
            "organization_id": organization_id,
            "role": role,
        }

    def list_organizations(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            return [
                {
                    "organization_id": r["organization_id"],
                    "name": r["name"],
                    "created_at": r["created_at"],
                }
                for r in conn.execute("SELECT * FROM organization").fetchall()
            ]

    def list_memberships(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            return [
                {
                    "username": r["username"],
                    "organization_id": r["organization_id"],
                    "role": r["role"],
                }
                for r in conn.execute("SELECT * FROM tenant_membership").fetchall()
            ]


__all__ = ["MultiTenantService"]
