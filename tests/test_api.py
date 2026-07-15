"""Tests for the REST API endpoints.

Covers: healthcheck, workflow listing, workflow enqueue, analytics summary,
provenance events, and API authentication enforcement.
"""

from __future__ import annotations

import sqlite3
import uuid
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

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

    S.init_db()
    yield
    keeper.close()


@pytest.fixture(autouse=True)
def _clear_singletons(tmp_path, monkeypatch):
    """Replace shared singletons with fresh instances backed by the test DB."""
    import accessibility_mgr.api.platform_api as api_mod
    from accessibility_mgr.services.authentication import AuthenticationService
    from accessibility_mgr.services.persistent_analytics import PersistentAnalyticsService
    from accessibility_mgr.services.persistent_provenance import PersistentProvenanceRegistry
    from accessibility_mgr.services.persistent_queue import PersistentWorkflowQueue

    test_db = tmp_path / "singleton_test.db"

    fresh_queue = PersistentWorkflowQueue(database_path=test_db)
    fresh_analytics = PersistentAnalyticsService(database_path=test_db)
    fresh_provenance = PersistentProvenanceRegistry(database_path=test_db)
    fresh_auth = AuthenticationService()

    monkeypatch.setattr(api_mod, "_queue", fresh_queue)
    monkeypatch.setattr(api_mod, "_analytics", fresh_analytics)
    monkeypatch.setattr(api_mod, "_provenance", fresh_provenance)
    monkeypatch.setattr(api_mod, "_auth", fresh_auth)

    yield


@pytest.fixture()
def api_client_no_auth(monkeypatch):
    """Create a TestClient with API auth disabled."""
    import accessibility_mgr.api.platform_api as api_mod
    monkeypatch.setattr(api_mod, "_require_api_key", False)
    return TestClient(api_mod.app)


@pytest.fixture()
def api_client_auth(monkeypatch):
    """Create a TestClient with API auth enabled and a registered key."""
    import accessibility_mgr.api.platform_api as api_mod
    monkeypatch.setattr(api_mod, "_require_api_key", True)
    api_mod._auth.register_api_token(
        owner="test-user",
        raw_token="test-api-key-12345",
        expiration_hours=24,
    )
    return TestClient(api_mod.app)


class TestHealthcheck:
    def test_health_returns_ok(self, api_client_no_auth):
        resp = api_client_no_auth.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "accessibility-operations-api"
        assert "version" in data


class TestWorkflowEndpoints:
    def test_list_workflows_empty(self, api_client_no_auth):
        resp = api_client_no_auth.get("/workflows")
        assert resp.status_code == 200
        assert resp.json()["jobs"] == []

    def test_enqueue_workflow(self, api_client_no_auth):
        resp = api_client_no_auth.post(
            "/workflows/enqueue",
            params={"workflow_name": "test-wf", "asset_id": 1, "priority": 5},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["workflow"] == "test-wf"
        assert data["asset_id"] == 1
        assert data["status"] == "queued"

    def test_list_workflows_after_enqueue(self, api_client_no_auth):
        api_client_no_auth.post(
            "/workflows/enqueue",
            params={"workflow_name": "wf1", "asset_id": 1},
        )
        resp = api_client_no_auth.get("/workflows")
        assert resp.status_code == 200
        jobs = resp.json()["jobs"]
        assert len(jobs) == 1
        assert jobs[0]["workflow_name"] == "wf1"


class TestAnalyticsEndpoint:
    def test_analytics_empty(self, api_client_no_auth):
        resp = api_client_no_auth.get("/analytics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_metrics"] == 0

    def test_analytics_after_recording(self, api_client_no_auth):
        import accessibility_mgr.api.platform_api as api_mod
        api_mod._analytics.record_metric(
            metric_name="test", metric_value=95.0, category="qa",
        )
        resp = api_client_no_auth.get("/analytics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_metrics"] == 1
        assert data["average_score"] == 95.0


class TestProvenanceEndpoint:
    def test_provenance_empty(self, api_client_no_auth):
        resp = api_client_no_auth.get("/provenance")
        assert resp.status_code == 200
        assert resp.json()["events"] == []

    def test_provenance_after_event(self, api_client_no_auth):
        import accessibility_mgr.api.platform_api as api_mod
        api_mod._provenance.register_event(
            asset_id=1, event_type="INGEST", summary="test",
        )
        resp = api_client_no_auth.get("/provenance")
        assert resp.status_code == 200
        events = resp.json()["events"]
        assert len(events) == 1


class TestAPIAuthentication:
    def test_no_key_returns_401(self, api_client_auth):
        resp = api_client_auth.get("/workflows")
        assert resp.status_code == 401
        assert "Missing X-API-Key" in resp.json()["detail"]

    def test_invalid_key_returns_401(self, api_client_auth):
        resp = api_client_auth.get(
            "/workflows",
            headers={"X-API-Key": "wrong-key"},
        )
        assert resp.status_code == 401
        assert "Invalid API key" in resp.json()["detail"]

    def test_valid_key_succeeds(self, api_client_auth):
        resp = api_client_auth.get(
            "/workflows",
            headers={"X-API-Key": "test-api-key-12345"},
        )
        assert resp.status_code == 200

    def test_enqueue_requires_auth(self, api_client_auth):
        resp = api_client_auth.post(
            "/workflows/enqueue",
            params={"workflow_name": "wf", "asset_id": 1},
        )
        assert resp.status_code == 401

    def test_enqueue_with_valid_key(self, api_client_auth):
        resp = api_client_auth.post(
            "/workflows/enqueue",
            params={"workflow_name": "wf", "asset_id": 1},
            headers={"X-API-Key": "test-api-key-12345"},
        )
        assert resp.status_code == 200

    def test_health_needs_no_auth(self, api_client_auth):
        resp = api_client_auth.get("/health")
        assert resp.status_code == 200

    def test_provenance_requires_auth(self, api_client_auth):
        resp = api_client_auth.get("/provenance")
        assert resp.status_code == 401

    def test_analytics_requires_auth(self, api_client_auth):
        resp = api_client_auth.get("/analytics")
        assert resp.status_code == 401
