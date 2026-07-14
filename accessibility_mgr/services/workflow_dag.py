"""Dependency-aware workflow DAG orchestration — SQLite-backed."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


def _default_db_path() -> Path:
    try:
        from ..db.schema import DB_PATH
        return DB_PATH
    except Exception:
        return Path("accessibility_mgr.db")


class WorkflowDAGService:
    """SQLite-backed dependency-aware orchestration engine."""

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
                """CREATE TABLE IF NOT EXISTS workflow_dag_node (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_name TEXT NOT NULL UNIQUE,
                    dependencies_json TEXT NOT NULL DEFAULT '[]',
                    retry_limit INTEGER NOT NULL DEFAULT 3,
                    status TEXT NOT NULL DEFAULT 'pending'
                )"""
            )

    def register_workflow(
        self,
        *,
        workflow_name: str,
        dependencies: list[str] | None = None,
        retry_limit: int = 3,
    ) -> dict[str, Any]:
        deps = dependencies or []
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO workflow_dag_node (workflow_name, dependencies_json, retry_limit, status) "
                "VALUES (?, ?, ?, 'pending')",
                (workflow_name, json.dumps(deps), retry_limit),
            )
        return {
            "workflow_name": workflow_name,
            "dependencies": deps,
            "retry_limit": retry_limit,
            "status": "pending",
        }

    def executable_workflows(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM workflow_dag_node WHERE status = 'pending'"
            ).fetchall()
            executable = []
            for row in rows:
                deps = json.loads(row["dependencies_json"])
                blocked = False
                for dep_name in deps:
                    dep = conn.execute(
                        "SELECT status FROM workflow_dag_node WHERE workflow_name = ?",
                        (dep_name,),
                    ).fetchone()
                    if dep and dep["status"] != "completed":
                        blocked = True
                        break
                if not blocked:
                    executable.append({
                        "workflow_name": row["workflow_name"],
                        "dependencies": deps,
                        "retry_limit": row["retry_limit"],
                        "status": row["status"],
                    })
            return executable

    def complete(self, workflow_name: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE workflow_dag_node SET status = 'completed' WHERE workflow_name = ?",
                (workflow_name,),
            )

    def fail(self, workflow_name: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE workflow_dag_node SET status = 'failed' WHERE workflow_name = ?",
                (workflow_name,),
            )

    def topology(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            return [
                {
                    "workflow_name": r["workflow_name"],
                    "dependencies": json.loads(r["dependencies_json"]),
                    "retry_limit": r["retry_limit"],
                    "status": r["status"],
                }
                for r in conn.execute(
                    "SELECT * FROM workflow_dag_node"
                ).fetchall()
            ]


__all__ = ["WorkflowDAGService"]
