"""Database migration and schema version management."""

from __future__ import annotations

from dataclasses import dataclass

from .sqlite_store import SQLiteStore


@dataclass(slots=True)
class Migration:
    version: int
    description: str
    sql: str


class MigrationManager:
    """Applies ordered schema migrations."""

    def __init__(self, store: SQLiteStore | None = None) -> None:
        self.store = store or SQLiteStore()
        self._initialize_version_table()

    def _initialize_version_table(self) -> None:
        self.store.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                description TEXT NOT NULL,
                applied_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    def applied_versions(self) -> set[int]:
        rows = self.store.fetch_all(
            "SELECT version FROM schema_version"
        )
        return {row["version"] for row in rows}

    def apply_migrations(
        self,
        migrations: list[Migration],
    ) -> list[int]:
        applied = self.applied_versions()
        executed: list[int] = []

        for migration in sorted(migrations, key=lambda m: m.version):
            if migration.version in applied:
                continue

            self.store.execute(migration.sql)

            self.store.execute(
                """
                INSERT INTO schema_version (
                    version,
                    description
                ) VALUES (?, ?)
                """,
                (migration.version, migration.description),
            )

            executed.append(migration.version)

        return executed


DEFAULT_MIGRATIONS = [
    Migration(
        version=1,
        description="Add artifact registry table",
        sql="""
        CREATE TABLE IF NOT EXISTS qa_artifact (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL,
            artifact_type TEXT NOT NULL,
            file_name TEXT NOT NULL,
            generated_by TEXT NOT NULL,
            metadata_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """,
    ),
    Migration(
        version=2,
        description="Add workflow queue table",
        sql="""
        CREATE TABLE IF NOT EXISTS workflow_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_name TEXT NOT NULL,
            asset_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            priority INTEGER NOT NULL DEFAULT 5,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """,
    ),
]


__all__ = [
    "Migration",
    "MigrationManager",
    "DEFAULT_MIGRATIONS",
]
