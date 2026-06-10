"""Operations analytics dashboard."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from nicegui import ui

from ..services.analytics import AnalyticsService
from ..services.artifact_retention import ArtifactRetentionService
from ..services.audit_log import AuditLogService
from ..services.compliance_reporting import ComplianceReportingService
from ..services.distributed_workers import DistributedWorkerRegistry
from ..services.event_stream import EventStreamService
from ..services.multi_tenant import MultiTenantService
from ..services.sla_monitoring import SLAMonitoringService
from ..services.workflow_dag import WorkflowDAGService
from .components import section_header


_analytics = AnalyticsService()
_sla = SLAMonitoringService()
_dag = WorkflowDAGService()
_tenants = MultiTenantService()
_retention = ArtifactRetentionService()
_audit = AuditLogService()
_workers = DistributedWorkerRegistry()
_events = EventStreamService()
_compliance = ComplianceReportingService()
_seeded = False

def _seed_once() -> None:
    global _seeded
    if _seeded:
        return

    _analytics.record_metric(
        metric_name="qa_accessibility_score",
        metric_value=98,
        category="qa",
        metadata={"pipeline": "epub_accessibility_pipeline"},
    )
    _analytics.record_metric(
        metric_name="metadata_validation_pass_rate",
        metric_value=94,
        category="governance",
    )
    _analytics.record_metric(
        metric_name="pipeline_retry_rate",
        metric_value=3,
        category="operations",
    )

    _dag.register_workflow(workflow_name="ingest")
    _dag.register_workflow(workflow_name="transform", dependencies=["ingest"])
    _dag.register_workflow(workflow_name="qa", dependencies=["transform"])

    _workers.register_node(node_id="worker-1", hostname="localhost")
    _events.subscribe(event_type="workflow_status", callback_url="http://localhost/webhook")
    _sla.register_workflow(workflow_name="ingest", asset_id=1, sla_minutes=30)
    _audit.record_event(
        event_type="dashboard_seeded",
        actor="system",
        payload={"source": "operations_dashboard"},
    )

    _seeded = True



def operations_dashboard_page(content_area: ui.element) -> None:
    """Render operational analytics dashboard."""
    _seed_once()

    content_area.clear()

    def _render() -> None:
        content_area.clear()

        summary = _analytics.summarize()
        sla_summary = _sla.health_summary()
        topo = _dag.topology()
        executable = _dag.executable_workflows()
        organizations = _tenants.list_organizations()
        memberships = _tenants.list_memberships()
        retention_records = _retention.evaluate_retention()
        audit_events = _audit.list_events()
        workers = _workers.list_nodes()
        stream_events = _events.list_events()
        subscriptions = _events.list_subscriptions()

        with content_area:
            section_header(
                "Operations Dashboard",
                "Operational KPI, workflow, and governance controls",
            )

            with ui.row().classes("w-full gap-3 flex-wrap mb-4"):
                ui.button("Run SLA Evaluation", on_click=lambda: (_sla.evaluate_slas(), _render())).classes(
                    "bg-blue-600 text-white"
                )

                def _complete_next() -> None:
                    if executable:
                        _dag.complete(executable[0]["workflow_name"])
                    _render()

                ui.button("Complete Next DAG Step", on_click=_complete_next).classes(
                    "bg-green-600 text-white"
                )

                def _publish_event() -> None:
                    _events.publish(
                        event_type="workflow_status",
                        payload={"status": "ok", "sequence": len(stream_events) + 1},
                    )
                    _render()

                ui.button("Publish Test Event", on_click=_publish_event).classes(
                    "bg-amber-600 text-white"
                )

                def _register_worker() -> None:
                    idx = len(workers) + 1
                    _workers.register_node(
                        node_id=f"worker-{idx}",
                        hostname=f"host-{idx}",
                    )
                    _render()

                ui.button("Register Worker", on_click=_register_worker).classes(
                    "bg-slate-700 text-white"
                )

            with ui.grid(columns=4).classes("w-full gap-4 mb-6"):
                with ui.card().classes("p-5 rounded-xl border border-slate-200"):
                    ui.label("Tracked Metrics").classes("text-sm text-slate-500")
                    ui.label(str(summary["total_metrics"])).classes("text-3xl font-bold text-slate-700")

                with ui.card().classes("p-5 rounded-xl border border-slate-200"):
                    ui.label("SLA Breaches").classes("text-sm text-slate-500")
                    ui.label(str(sla_summary["sla_breaches"])).classes("text-3xl font-bold text-red-600")

                with ui.card().classes("p-5 rounded-xl border border-slate-200"):
                    ui.label("Workers Online").classes("text-sm text-slate-500")
                    online = len([n for n in workers if n.get("status") == "online"])
                    ui.label(str(online)).classes("text-3xl font-bold text-green-600")

                with ui.card().classes("p-5 rounded-xl border border-slate-200"):
                    ui.label("Stream Events").classes("text-sm text-slate-500")
                    ui.label(str(len(stream_events))).classes("text-3xl font-bold text-indigo-600")

            with ui.grid(columns=2).classes("w-full gap-4"):
                with ui.card().classes("p-5 rounded-xl border border-slate-200"):
                    ui.label("Workflow DAG").classes("text-base font-semibold text-slate-700 mb-2")
                    ui.label(f"Executable: {len(executable)}").classes("text-xs text-slate-500 mb-2")
                    for node in topo:
                        with ui.row().classes("items-center justify-between border-b border-slate-100 py-1"):
                            ui.label(node["workflow_name"]).classes("text-sm text-slate-700")
                            ui.badge(node["status"]).classes("text-xs bg-slate-100 text-slate-700")

                with ui.card().classes("p-5 rounded-xl border border-slate-200"):
                    ui.label("SLA Tracking").classes("text-base font-semibold text-slate-700 mb-2")
                    records = _sla.evaluate_slas()
                    if not records:
                        ui.label("No tracked workflows.").classes("text-sm text-slate-400")
                    for record in records:
                        with ui.row().classes("items-center justify-between border-b border-slate-100 py-1"):
                            ui.label(f"{record['workflow_name']} (asset {record['asset_id']})").classes(
                                "text-sm text-slate-700"
                            )
                            ui.badge("breached" if record["breached"] else "healthy").classes(
                                "text-xs "
                                + ("bg-red-100 text-red-700" if record["breached"] else "bg-green-100 text-green-700")
                            )

                with ui.card().classes("p-5 rounded-xl border border-slate-200"):
                    ui.label("Workers & Event Stream").classes("text-base font-semibold text-slate-700 mb-2")
                    ui.label(f"Subscriptions: {len(subscriptions)}").classes("text-xs text-slate-500")
                    ui.label(f"Events: {len(stream_events)}").classes("text-xs text-slate-500 mb-2")
                    for node in workers[-5:]:
                        with ui.row().classes("items-center justify-between border-b border-slate-100 py-1"):
                            ui.label(node["node_id"]).classes("text-sm text-slate-700")
                            ui.badge(node["status"]).classes("text-xs bg-slate-100 text-slate-700")

                with ui.card().classes("p-5 rounded-xl border border-slate-200"):
                    ui.label("Tenancy & Retention").classes("text-base font-semibold text-slate-700 mb-2")

                    def _create_org() -> None:
                        idx = len(organizations) + 1
                        org = _tenants.create_organization(f"Organization {idx}")
                        _tenants.add_member(
                            username=f"operator{idx}",
                            organization_id=org.organization_id,
                            role="operator",
                        )
                        _render()

                    ui.button("Add Sample Organization", on_click=_create_org).props("flat dense").classes(
                        "text-blue-600"
                    )

                    def _register_retention() -> None:
                        p = Path("artifacts") / f"retention-{uuid4().hex[:8]}.tmp"
                        p.parent.mkdir(parents=True, exist_ok=True)
                        p.write_text("retention marker", encoding="utf-8")
                        _retention.register_artifact(str(p), retention_days=1)
                        _render()

                    ui.button("Register Artifact", on_click=_register_retention).props("flat dense").classes(
                        "text-indigo-600"
                    )
                    ui.label(f"Organizations: {len(organizations)}").classes("text-xs text-slate-500")
                    ui.label(f"Memberships: {len(memberships)}").classes("text-xs text-slate-500")
                    ui.label(f"Artifacts tracked: {len(retention_records)}").classes("text-xs text-slate-500")

            with ui.card().classes("w-full p-5 rounded-xl border border-slate-200 mt-4"):
                ui.label("Audit & Compliance").classes("text-base font-semibold text-slate-700 mb-3")

                with ui.row().classes("gap-2 mb-2"):
                    def _export_provenance() -> None:
                        report = _compliance.generate_provenance_export()
                        _audit.record_event(
                            event_type="provenance_export_requested",
                            actor="user",
                            payload={"signature": report.get("signature")},
                        )
                        _render()

                    ui.button("Generate Provenance Export", on_click=_export_provenance).props("flat dense").classes(
                        "text-green-700"
                    )

                    def _export_governance() -> None:
                        report = _compliance.generate_governance_report()
                        _audit.record_event(
                            event_type="governance_report_requested",
                            actor="user",
                            payload={"signature": report.get("signature")},
                        )
                        _render()

                    ui.button("Generate Governance Report", on_click=_export_governance).props("flat dense").classes(
                        "text-amber-700"
                    )

                for event in audit_events[-8:]:
                    with ui.row().classes("items-center justify-between border-b border-slate-100 py-1"):
                        ui.label(f"{event['event_type']} ({event['actor']})").classes(
                            "text-sm text-slate-700"
                        )
                        ui.label(event["created_at"][:19]).classes("text-xs text-slate-400 font-mono")

    _render()
