"""Shared test fixtures for the Accessibility Project Manager test suite."""

from __future__ import annotations

import sqlite3
import uuid
from contextlib import contextmanager

import pytest

from accessibility_mgr.db import queries as Q
from accessibility_mgr.db import schema as S


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    """Provide a fresh in-memory SQLite database for every test."""
    db_uri = f"file:testdb_{uuid.uuid4().hex}?mode=memory&cache=shared"
    keeper = sqlite3.connect(db_uri, uri=True)
    keeper.row_factory = sqlite3.Row
    keeper.execute("PRAGMA foreign_keys = ON")
    keeper.execute("PRAGMA journal_mode = WAL")

    @contextmanager
    def _get_conn():
        conn = sqlite3.connect(db_uri, uri=True)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    monkeypatch.setattr(S, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(S, "PRINTS_DIR", tmp_path / "prints_files")
    monkeypatch.setattr(S, "FILES_DIR", tmp_path / "job_files")
    monkeypatch.setattr(S, "BACKUPS_DIR", tmp_path / "backups")
    monkeypatch.setattr(S, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(S, "get_conn", _get_conn)

    monkeypatch.setattr(Q, "PRINTS_DIR", tmp_path / "prints_files")
    monkeypatch.setattr(Q, "FILES_DIR", tmp_path / "job_files")
    monkeypatch.setattr(Q, "ARTIFACTS_DIR", tmp_path / "artifacts")
    monkeypatch.setattr(Q, "get_conn", _get_conn)

    S.init_db()
    yield
    keeper.close()


@pytest.fixture()
def tmp_db_path(tmp_path):
    """Return a temporary database path for service-level tests."""
    return tmp_path / "test_service.db"
