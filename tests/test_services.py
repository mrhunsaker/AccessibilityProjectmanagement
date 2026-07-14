"""Comprehensive tests for the services layer.

Covers: RBAC, Authentication, SLA Monitoring, Workflow DAG,
Persistent Queue, Persistent Analytics, Persistent Provenance,
Artifact Retention, Audit Log, Event Stream, Distributed Workers,
Multi-Tenant, Metadata Validation, Compliance Reporting,
Workflow Queue, Worker Runtime, and Execution Service.
"""

from __future__ import annotations

from pathlib import Path

# ── RBAC ───────────────────────────────────────────────────────────────────────

class TestRBACService:
    def test_seed_roles_created(self):
        from accessibility_mgr.services.rbac import RBACService
        svc = RBACService()
        roles = svc.list_roles()
        names = {r["name"] for r in roles}
        assert "administrator" in names
        assert "operator" in names
        assert "reviewer" in names

    def test_administrator_has_full_permissions(self):
        from accessibility_mgr.services.rbac import RBACService
        svc = RBACService()
        admin = svc.get_role("administrator")
        assert admin is not None
        assert "qa.execute" in admin.permissions
        assert "qa.review" in admin.permissions
        assert "governance.manage" in admin.permissions
        assert "workflow.manage" in admin.permissions
        assert "analytics.view" in admin.permissions
        assert "rbac.manage" in admin.permissions

    def test_operator_lacks_review_permission(self):
        from accessibility_mgr.services.rbac import RBACService
        svc = RBACService()
        operator = svc.get_role("operator")
        assert operator is not None
        assert "qa.execute" in operator.permissions
        assert "qa.review" not in operator.permissions

    def test_reviewer_lacks_execute_permission(self):
        from accessibility_mgr.services.rbac import RBACService
        svc = RBACService()
        reviewer = svc.get_role("reviewer")
        assert reviewer is not None
        assert "qa.review" in reviewer.permissions
        assert "qa.execute" not in reviewer.permissions

    def test_authorize_with_matching_permission(self):
        from accessibility_mgr.services.rbac import RBACService, UserIdentity
        svc = RBACService()
        user = UserIdentity(username="alice", roles=[svc.get_role("operator")])
        assert svc.authorize(user, "qa.execute") is True

    def test_authorize_denies_missing_permission(self):
        from accessibility_mgr.services.rbac import RBACService, UserIdentity
        svc = RBACService()
        user = UserIdentity(username="bob", roles=[svc.get_role("reviewer")])
        assert svc.authorize(user, "qa.execute") is False

    def test_authorize_with_no_roles(self):
        from accessibility_mgr.services.rbac import RBACService, UserIdentity
        svc = RBACService()
        user = UserIdentity(username="nobody", roles=[])
        assert svc.authorize(user, "analytics.view") is False

    def test_register_custom_role(self):
        from accessibility_mgr.services.rbac import RBACService, Role
        svc = RBACService()
        custom = Role(name="custom", permissions={"custom.perm"})
        svc.register_role(custom)
        retrieved = svc.get_role("custom")
        assert retrieved is not None
        assert "custom.perm" in retrieved.permissions

    def test_get_nonexistent_role(self):
        from accessibility_mgr.services.rbac import RBACService
        svc = RBACService()
        assert svc.get_role("nonexistent") is None


# ── Authentication ─────────────────────────────────────────────────────────────

class TestAuthenticationService:
    def test_create_and_validate_token(self):
        from accessibility_mgr.services.authentication import AuthenticationService
        svc = AuthenticationService()
        result = svc.create_api_token(owner="test-user", expiration_hours=24)
        assert "token" in result
        assert "token_id" in result
        assert svc.validate_token(result["token"]) is True

    def test_validate_rejects_wrong_token(self):
        from accessibility_mgr.services.authentication import AuthenticationService
        svc = AuthenticationService()
        svc.create_api_token(owner="test-user")
        assert svc.validate_token("wrong-token-value") is False

    def test_register_and_validate_token(self):
        from accessibility_mgr.services.authentication import AuthenticationService
        svc = AuthenticationService()
        raw = "my-custom-api-key-12345"
        svc.register_api_token(owner="config-user", raw_token=raw, expiration_hours=24)
        assert svc.validate_token(raw) is True

    def test_list_tokens(self):
        from accessibility_mgr.services.authentication import AuthenticationService
        svc = AuthenticationService()
        svc.create_api_token(owner="user1")
        svc.create_api_token(owner="user2")
        tokens = svc.list_tokens()
        assert len(tokens) == 2
        assert tokens[0]["owner"] == "user1"
        assert tokens[1]["owner"] == "user2"

    def test_create_session(self):
        from accessibility_mgr.services.authentication import AuthenticationService
        svc = AuthenticationService()
        session = svc.create_session(username="alice")
        assert session.username == "alice"
        assert session.session_id
        assert session.expires_at

    def test_validate_expired_token(self):
        from accessibility_mgr.services.authentication import AuthenticationService
        svc = AuthenticationService()
        result = svc.create_api_token(owner="expired-user", expiration_hours=-1)
        assert svc.validate_token(result["token"]) is False


# ── SLA Monitoring ─────────────────────────────────────────────────────────────

class TestSLAMonitoringService:
    def test_register_and_evaluate_workflow(self, tmp_db_path):
        from accessibility_mgr.services.sla_monitoring import SLAMonitoringService
        svc = SLAMonitoringService(database_path=tmp_db_path)
        result = svc.register_workflow(
            workflow_name="test-flow",
            asset_id=42,
            sla_minutes=30,
        )
        assert result["workflow_name"] == "test-flow"
        assert result["breached"] is False

        slas = svc.evaluate_slas()
        assert len(slas) == 1
        assert slas[0]["breached"] is False

    def test_health_summary(self, tmp_db_path):
        from accessibility_mgr.services.sla_monitoring import SLAMonitoringService
        svc = SLAMonitoringService(database_path=tmp_db_path)
        svc.register_workflow(workflow_name="flow-a", asset_id=1)
        svc.register_workflow(workflow_name="flow-b", asset_id=2)
        summary = svc.health_summary()
        assert summary["tracked_workflows"] == 2
        assert summary["sla_breaches"] == 0
        assert summary["healthy_workflows"] == 2

    def test_list_escalations_empty(self, tmp_db_path):
        from accessibility_mgr.services.sla_monitoring import SLAMonitoringService
        svc = SLAMonitoringService(database_path=tmp_db_path)
        assert svc.list_escalations() == []


# ── Workflow DAG ───────────────────────────────────────────────────────────────

class TestWorkflowDAGService:
    def test_register_and_discover_executable(self, tmp_db_path):
        from accessibility_mgr.services.workflow_dag import WorkflowDAGService
        svc = WorkflowDAGService(database_path=tmp_db_path)
        svc.register_workflow(workflow_name="step-a")
        svc.register_workflow(workflow_name="step-b", dependencies=["step-a"])
        executable = svc.executable_workflows()
        names = {w["workflow_name"] for w in executable}
        assert "step-a" in names
        assert "step-b" not in names

    def test_complete_unlocks_dependents(self, tmp_db_path):
        from accessibility_mgr.services.workflow_dag import WorkflowDAGService
        svc = WorkflowDAGService(database_path=tmp_db_path)
        svc.register_workflow(workflow_name="step-a")
        svc.register_workflow(workflow_name="step-b", dependencies=["step-a"])
        svc.complete("step-a")
        executable = svc.executable_workflows()
        names = {w["workflow_name"] for w in executable}
        assert "step-b" in names

    def test_fail_workflow(self, tmp_db_path):
        from accessibility_mgr.services.workflow_dag import WorkflowDAGService
        svc = WorkflowDAGService(database_path=tmp_db_path)
        svc.register_workflow(workflow_name="step-a")
        svc.fail("step-a")
        topo = svc.topology()
        assert topo[0]["status"] == "failed"

    def test_topology(self, tmp_db_path):
        from accessibility_mgr.services.workflow_dag import WorkflowDAGService
        svc = WorkflowDAGService(database_path=tmp_db_path)
        svc.register_workflow(workflow_name="x", dependencies=[], retry_limit=5)
        topo = svc.topology()
        assert len(topo) == 1
        assert topo[0]["retry_limit"] == 5


# ── Persistent Queue ───────────────────────────────────────────────────────────

class TestPersistentWorkflowQueue:
    def test_enqueue_and_list(self, tmp_db_path):
        from accessibility_mgr.services.persistent_queue import PersistentWorkflowQueue
        svc = PersistentWorkflowQueue(database_path=tmp_db_path)
        job = svc.enqueue(workflow_name="test-wf", asset_id=1, priority=3)
        assert job.workflow_name == "test-wf"
        assert job.status == "queued"
        jobs = svc.list_jobs()
        assert len(jobs) == 1

    def test_next_job_returns_highest_priority(self, tmp_db_path):
        from accessibility_mgr.services.persistent_queue import PersistentWorkflowQueue
        svc = PersistentWorkflowQueue(database_path=tmp_db_path)
        svc.enqueue(workflow_name="low-pri", asset_id=1, priority=10)
        svc.enqueue(workflow_name="high-pri", asset_id=2, priority=1)
        job = svc.next_job()
        assert job is not None
        assert job.workflow_name == "high-pri"
        assert job.status == "running"

    def test_complete_job(self, tmp_db_path):
        from accessibility_mgr.services.persistent_queue import PersistentWorkflowQueue
        svc = PersistentWorkflowQueue(database_path=tmp_db_path)
        svc.enqueue(workflow_name="wf", asset_id=1)
        running = svc.next_job()
        svc.complete_job(running)
        assert running.status == "completed"

    def test_fail_job(self, tmp_db_path):
        from accessibility_mgr.services.persistent_queue import PersistentWorkflowQueue
        svc = PersistentWorkflowQueue(database_path=tmp_db_path)
        svc.enqueue(workflow_name="wf", asset_id=1)
        running = svc.next_job()
        svc.fail_job(running)
        assert running.status == "failed"

    def test_next_job_returns_none_when_empty(self, tmp_db_path):
        from accessibility_mgr.services.persistent_queue import PersistentWorkflowQueue
        svc = PersistentWorkflowQueue(database_path=tmp_db_path)
        assert svc.next_job() is None


# ── Persistent Analytics ───────────────────────────────────────────────────────

class TestPersistentAnalyticsService:
    def test_record_and_summarize(self, tmp_db_path):
        from accessibility_mgr.services.persistent_analytics import PersistentAnalyticsService
        svc = PersistentAnalyticsService(database_path=tmp_db_path)
        svc.record_metric(metric_name="score", metric_value=95.0, category="qa")
        svc.record_metric(metric_name="score", metric_value=88.0, category="qa")
        summary = svc.summarize()
        assert summary["total_metrics"] == 2
        assert summary["average_score"] == 91.5
        assert summary["categories"]["qa"] == 2

    def test_list_metrics(self, tmp_db_path):
        from accessibility_mgr.services.persistent_analytics import PersistentAnalyticsService
        svc = PersistentAnalyticsService(database_path=tmp_db_path)
        svc.record_metric(metric_name="m1", metric_value=1.0, category="c1")
        metrics = svc.list_metrics()
        assert len(metrics) == 1
        assert metrics[0]["metric_name"] == "m1"

    def test_empty_summary(self, tmp_db_path):
        from accessibility_mgr.services.persistent_analytics import PersistentAnalyticsService
        svc = PersistentAnalyticsService(database_path=tmp_db_path)
        summary = svc.summarize()
        assert summary["total_metrics"] == 0
        assert summary["average_score"] == 0


# ── Persistent Provenance ──────────────────────────────────────────────────────

class TestPersistentProvenanceRegistry:
    def test_register_and_list_events(self, tmp_db_path):
        from accessibility_mgr.services.persistent_provenance import PersistentProvenanceRegistry
        svc = PersistentProvenanceRegistry(database_path=tmp_db_path)
        svc.register_event(asset_id=1, event_type="INGEST", summary="File ingested")
        svc.register_event(asset_id=2, event_type="QA_RUN", summary="Ace check passed")
        events = svc.list_events()
        assert len(events) == 2

    def test_filter_by_asset_id(self, tmp_db_path):
        from accessibility_mgr.services.persistent_provenance import PersistentProvenanceRegistry
        svc = PersistentProvenanceRegistry(database_path=tmp_db_path)
        svc.register_event(asset_id=1, event_type="INGEST", summary="a")
        svc.register_event(asset_id=2, event_type="QA_RUN", summary="b")
        events = svc.list_events(asset_id=1)
        assert len(events) == 1
        assert events[0]["asset_id"] == 1


# ── Artifact Retention ─────────────────────────────────────────────────────────

class TestArtifactRetentionService:
    def test_register_and_evaluate(self, tmp_db_path):
        from accessibility_mgr.services.artifact_retention import ArtifactRetentionService
        svc = ArtifactRetentionService(database_path=tmp_db_path)
        svc.register_artifact("/tmp/test.txt", retention_days=30)
        records = svc.evaluate_retention()
        assert len(records) == 1
        assert records[0]["status"] == "active"

    def test_cleanup_expired(self, tmp_db_path):
        from accessibility_mgr.services.artifact_retention import ArtifactRetentionService
        svc = ArtifactRetentionService(database_path=tmp_db_path)
        # Register artifact and manually mark it expired
        svc.register_artifact("/tmp/expired.txt", retention_days=0)
        svc.evaluate_retention()  # Should mark as expired
        removed = svc.cleanup_expired()
        assert len(removed) == 1


# ── Audit Log ──────────────────────────────────────────────────────────────────

class TestAuditLogService:
    def test_record_and_verify(self, tmp_db_path):
        from accessibility_mgr.services.audit_log import AuditLogService
        svc = AuditLogService(database_path=tmp_db_path)
        result = svc.record_event(
            event_type="login",
            actor="alice",
            payload={"ip": "127.0.0.1"},
        )
        assert result["event_type"] == "login"
        assert result["actor"] == "alice"
        assert result["event_hash"]
        assert svc.verify_integrity() is True

    def test_list_events(self, tmp_db_path):
        from accessibility_mgr.services.audit_log import AuditLogService
        svc = AuditLogService(database_path=tmp_db_path)
        svc.record_event(event_type="e1", actor="a1", payload={})
        svc.record_event(event_type="e2", actor="a2", payload={})
        events = svc.list_events()
        assert len(events) == 2


# ── Event Stream ───────────────────────────────────────────────────────────────

class TestEventStreamService:
    def test_subscribe_and_publish(self, tmp_db_path):
        from accessibility_mgr.services.event_stream import EventStreamService
        svc = EventStreamService(database_path=tmp_db_path)
        svc.subscribe(event_type="job.completed", callback_url="http://hook/test")
        result = svc.publish(event_type="job.completed", payload={"job_id": 1})
        assert result["event_type"] == "job.completed"
        events = svc.list_events()
        assert len(events) == 1
        subs = svc.list_subscriptions()
        assert len(subs) == 1


# ── Distributed Workers ────────────────────────────────────────────────────────

class TestDistributedWorkerRegistry:
    def test_register_and_list(self, tmp_db_path):
        from accessibility_mgr.services.distributed_workers import DistributedWorkerRegistry
        svc = DistributedWorkerRegistry(database_path=tmp_db_path)
        svc.register_node(node_id="node-1", hostname="worker-1")
        nodes = svc.list_nodes()
        assert len(nodes) == 1
        assert nodes[0]["node_id"] == "node-1"

    def test_set_status(self, tmp_db_path):
        from accessibility_mgr.services.distributed_workers import DistributedWorkerRegistry
        svc = DistributedWorkerRegistry(database_path=tmp_db_path)
        svc.register_node(node_id="n1", hostname="h1")
        svc.set_status("n1", "offline")
        nodes = svc.list_nodes()
        assert nodes[0]["status"] == "offline"


# ── Multi-Tenant ───────────────────────────────────────────────────────────────

class TestMultiTenantService:
    def test_create_organization(self, tmp_db_path):
        from accessibility_mgr.services.multi_tenant import MultiTenantService
        svc = MultiTenantService(database_path=tmp_db_path)
        org = svc.create_organization("Test Org")
        assert org["name"] == "Test Org"
        assert org["organization_id"]
        orgs = svc.list_organizations()
        assert len(orgs) == 1

    def test_add_member(self, tmp_db_path):
        from accessibility_mgr.services.multi_tenant import MultiTenantService
        svc = MultiTenantService(database_path=tmp_db_path)
        svc.create_organization("Org1")
        svc.add_member(username="alice", organization_id="org-1", role="admin")
        members = svc.list_memberships()
        assert len(members) == 1
        assert members[0]["username"] == "alice"


# ── Metadata Validation ────────────────────────────────────────────────────────

class TestMetadataValidationService:
    def test_valid_dublin_core(self):
        from accessibility_mgr.services.metadata_validation import MetadataValidationService
        svc = MetadataValidationService()
        result = svc.validate_dublin_core({
            "title": "My Book",
            "creator": "Author",
            "language": "en",
            "identifier": "12345",
        })
        assert result.valid is True
        assert len(result.issues) == 0

    def test_missing_required_fields(self):
        from accessibility_mgr.services.metadata_validation import MetadataValidationService
        svc = MetadataValidationService()
        result = svc.validate_dublin_core({})
        assert result.valid is False
        error_fields = {i.field_name for i in result.issues if i.severity == "error"}
        assert "title" in error_fields
        assert "creator" in error_fields

    def test_unapproved_language(self):
        from accessibility_mgr.services.metadata_validation import MetadataValidationService
        svc = MetadataValidationService()
        result = svc.validate_dublin_core({
            "title": "Test",
            "creator": "Author",
            "language": "xx",
            "identifier": "1",
        })
        # Warnings are included in issues; the validation result marks
        # the metadata as invalid when any issues exist (error or warning).
        assert result.valid is False
        assert any(i.severity == "warning" for i in result.issues)

    def test_epub_accessibility_valid(self):
        from accessibility_mgr.services.metadata_validation import MetadataValidationService
        svc = MetadataValidationService()
        result = svc.validate_epub_accessibility({
            "schema:accessMode": "textual",
            "schema:accessHazard": "none",
            "schema:accessibilitySummary": "Fully accessible",
        })
        assert result.valid is True

    def test_epub_accessibility_invalid_hazard(self):
        from accessibility_mgr.services.metadata_validation import MetadataValidationService
        svc = MetadataValidationService()
        result = svc.validate_epub_accessibility({
            "schema:accessHazard": "invalid_hazard",
        })
        assert result.valid is False


# ── Compliance Reporting ───────────────────────────────────────────────────────

class TestComplianceReportingService:
    def test_generate_provenance_export(self, tmp_db_path, monkeypatch):
        from accessibility_mgr.services.compliance_reporting import ComplianceReportingService
        monkeypatch.setenv("ACCESSMAN_SIGNING_KEY", "")
        svc = ComplianceReportingService()
        export = svc.generate_provenance_export()
        assert export["export_type"] == "provenance"
        assert export["signature"]
        assert export["signature_algorithm"] == "SHA256-CHECKSUM-UNSIGNED"

    def test_signed_export_with_key(self, tmp_db_path, monkeypatch):
        from accessibility_mgr.services.compliance_reporting import ComplianceReportingService
        monkeypatch.setenv("ACCESSMAN_SIGNING_KEY", "test-signing-key-12345")
        svc = ComplianceReportingService()
        export = svc.generate_provenance_export()
        assert export["signature_algorithm"] == "HMAC-SHA256"

    def test_verify_signature(self, tmp_db_path, monkeypatch):
        from accessibility_mgr.services.compliance_reporting import ComplianceReportingService
        monkeypatch.setenv("ACCESSMAN_SIGNING_KEY", "verify-key")
        svc = ComplianceReportingService()
        payload = {"events": [], "generated_at": "2026-01-01T00:00:00"}
        sig, algo = svc._sign_payload(payload)
        assert svc.verify_signature(payload, sig, algorithm=algo) is True
        assert svc.verify_signature(payload, "wrong-sig", algorithm=algo) is False

    def test_governance_report(self, tmp_db_path, monkeypatch):
        from accessibility_mgr.services.compliance_reporting import ComplianceReportingService
        monkeypatch.setenv("ACCESSMAN_SIGNING_KEY", "")
        svc = ComplianceReportingService()
        report = svc.generate_governance_report()
        assert report["export_type"] == "governance"


# ── Execution Service ──────────────────────────────────────────────────────────

class TestExecutionService:
    def test_run_allowed_command(self):
        from accessibility_mgr.services.execution_service import ExecutionService
        result = ExecutionService.run_command(["which", "python3"], timeout=10)
        assert result.success is True

    def test_reject_disallowed_command(self):
        from accessibility_mgr.services.execution_service import ExecutionService
        result = ExecutionService.run_command(["rm", "-rf", "/tmp/test"], timeout=5)
        assert result.success is False
        assert "not in the permitted allowlist" in result.output

    def test_check_tool_available(self):
        from accessibility_mgr.services.execution_service import ExecutionService
        assert ExecutionService.check_tool_available("python3") is True

    def test_check_tool_unavailable(self):
        from accessibility_mgr.services.execution_service import ExecutionService
        assert ExecutionService.check_tool_available("nonexistent_tool_xyz") is False


# ── Worker Runtime ─────────────────────────────────────────────────────────────

class TestWorkerRuntime:
    def test_worker_processes_job(self):
        import tempfile
        import time

        from accessibility_mgr.services.persistent_queue import PersistentWorkflowQueue
        from accessibility_mgr.services.worker_runtime import WorkerRuntime

        db = Path(tempfile.mktemp(suffix=".db"))
        queue = PersistentWorkflowQueue(database_path=db)
        queue.enqueue(workflow_name="test-wf", asset_id=1)

        processed = []

        def handler(job):
            processed.append(job.workflow_name)

        runtime = WorkerRuntime(queue_service=queue)
        runtime.start(handler, poll_interval=0.1)
        time.sleep(0.5)
        runtime.stop()

        assert "test-wf" in processed

    def test_worker_handles_failure(self):
        import tempfile
        import time

        from accessibility_mgr.services.persistent_queue import PersistentWorkflowQueue
        from accessibility_mgr.services.worker_runtime import WorkerRuntime

        db = Path(tempfile.mktemp(suffix=".db"))
        queue = PersistentWorkflowQueue(database_path=db)
        queue.enqueue(workflow_name="fail-wf", asset_id=1)

        def handler(job):
            raise RuntimeError("boom")

        runtime = WorkerRuntime(queue_service=queue)
        runtime.start(handler, poll_interval=0.1)
        time.sleep(0.5)
        runtime.stop()

        executions = runtime.list_executions()
        assert any(e["status"] == "failed" for e in executions)


# ── In-Memory Analytics (base class) ──────────────────────────────────────────

class TestAnalyticsService:
    def test_record_and_summarize(self):
        from accessibility_mgr.services.analytics import AnalyticsService
        svc = AnalyticsService()
        svc.record_metric(metric_name="m1", metric_value=90.0, category="qa")
        svc.record_metric(metric_name="m2", metric_value=80.0, category="ops")
        summary = svc.summarize()
        assert summary["total_metrics"] == 2
        assert summary["average_score"] == 85.0
        assert "qa" in summary["categories"]
        assert "ops" in summary["categories"]

    def test_empty_summarize(self):
        from accessibility_mgr.services.analytics import AnalyticsService
        svc = AnalyticsService()
        summary = svc.summarize()
        assert summary["total_metrics"] == 0
        assert summary["average_score"] == 0

    def test_list_metrics(self):
        from accessibility_mgr.services.analytics import AnalyticsService
        svc = AnalyticsService()
        svc.record_metric(metric_name="x", metric_value=1.0, category="c")
        metrics = svc.list_metrics()
        assert len(metrics) == 1
        assert metrics[0]["metric_name"] == "x"


# ── In-Memory Provenance (base class) ─────────────────────────────────────────

class TestProvenanceRegistry:
    def test_register_and_list(self):
        from accessibility_mgr.services.provenance_registry import ProvenanceRegistry
        svc = ProvenanceRegistry()
        svc.register_event(asset_id=1, event_type="INGEST", summary="ok")
        events = svc.list_events()
        assert len(events) == 1

    def test_filter_by_asset(self):
        from accessibility_mgr.services.provenance_registry import ProvenanceRegistry
        svc = ProvenanceRegistry()
        svc.register_event(asset_id=1, event_type="a", summary="1")
        svc.register_event(asset_id=2, event_type="b", summary="2")
        events = svc.list_events(asset_id=1)
        assert len(events) == 1
