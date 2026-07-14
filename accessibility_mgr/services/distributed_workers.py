"""Distributed worker coordination primitives — SQLite-backed."""

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


class DistributedWorkerRegistry:
    """SQLite-backed registry for distributed orchestration workers."""

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
                """CREATE TABLE IF NOT EXISTS distributed_worker_node (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id TEXT NOT NULL UNIQUE,
                    hostname TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'online',
                    registered_at TEXT NOT NULL
                )"""
            )

    def register_node(
        self,
        *,
        node_id: str,
        hostname: str,
    ) -> dict[str, Any]:
        registered_at = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO distributed_worker_node (node_id, hostname, status, registered_at) "
                "VALUES (?, ?, 'online', ?)",
                (node_id, hostname, registered_at),
            )
        return {
            "node_id": node_id,
            "hostname": hostname,
            "status": "online",
            "registered_at": registered_at,
        }

    def set_status(self, node_id: str, status: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE distributed_worker_node SET status = ? WHERE node_id = ?",
                (status, node_id),
            )

    def list_nodes(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            return [
                {
                    "node_id": r["node_id"],
                    "hostname": r["hostname"],
                    "status": r["status"],
                    "registered_at": r["registered_at"],
                }
                for r in conn.execute("SELECT * FROM distributed_worker_node").fetchall()
            ]


__all__ = ["DistributedWorkerRegistry"]
