"""Operations analytics dashboard."""

from __future__ import annotations

from nicegui import ui

from ..db import queries as Q
from ..services.artifact_retention import ArtifactRetentionService
from ..services.audit_log import AuditLogService
from ..services.compliance_reporting import ComplianceReportingService
from ..services.distributed_workers import DistributedWorkerRegistry
from ..services.event_stream import EventStreamService
from ..services.multi_tenant import MultiTenantService
from ..services.singletons import analytics as _analytics
from ..services.sla_monitoring import SLAMonitoringService
from ..services.workflow_dag import WorkflowDAGService
from .components import notify_error, notify_success, section_header


_sla = SLAMonitoringService()
_dag = WorkflowDAGService()
_tenants = MultiTenantService()
_retention = ArtifactRetentionService()
_audit = AuditLogService()
_workers = DistributedWorkerRegistry()
_events = EventStreamService()
_compliance = ComplianceReportingService()



def operations_dashboard_page(content_area: ui.element) -> None:
    """Render operational analytics dashboard."""
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

                def _publish_event_form() -> None:
                    with ui.dialog() as d, ui.card().classes("p-6 gap-3 w-[440px]"):
                        ui.label("Publish Platform Event").classes("text-lg font-bold text-slate-800")
                        etype_inp = ui.input("Event Type*", placeholder="e.g. job_completed, pipeline_failed").classes("w-full")
                        payload_inp = ui.textarea("Payload (JSON)", placeholder='{"job_id": 42, "status": "ok"}').classes("w-full")

                        def _do_publish() -> None:
                            import json as _json
                            etype = etype_inp.value.strip()
                            if not etype:
                                notify_error("Event type is required.")
                                return
                            raw = payload_inp.value.strip()
                            try:
                                payload = _json.loads(raw) if raw else {}
                            except ValueError:
                                notify_error("Payload must be valid JSON or empty.")
                                return
                            _events.publish(event_type=etype, payload=payload)
                            d.close()
                            notify_success(f"Event '{etype}' published.")
                            _render()

                        with ui.row().classes("justify-end gap-2 mt-2"):
                            ui.button("Cancel", on_click=d.close).props("flat").classes("text-slate-500")
                            ui.button("Publish", on_click=_do_publish).classes("bg-amber-600 text-white")
                    d.open()

                ui.button("＋ Publish Event", on_click=_publish_event_form).classes("bg-amber-600 text-white")

                def _register_worker_form() -> None:
                    with ui.dialog() as d, ui.card().classes("p-6 gap-3 w-[440px]"):
                        ui.label("Register Worker Node").classes("text-lg font-bold text-slate-800")
                        nid_inp = ui.input("Node ID*", placeholder="e.g. worker-prod-01").classes("w-full")
                        host_inp = ui.input("Hostname*", placeholder="e.g. prod-server-01.internal").classes("w-full")

                        def _do_register() -> None:
                            nid = nid_inp.value.strip()
                            host = host_inp.value.strip()
                            if not nid or not host:
                                notify_error("Node ID and hostname are required.")
                                return
                            _workers.register_node(node_id=nid, hostname=host)
                            _audit.record_event(event_type="worker_registered", actor="operator",
                                                payload={"node_id": nid, "hostname": host})
                            d.close()
                            notify_success(f"Worker '{nid}' registered.")
                            _render()

                        with ui.row().classes("justify-end gap-2 mt-2"):
                            ui.button("Cancel", on_click=d.close).props("flat").classes("text-slate-500")
                            ui.button("Register", on_click=_do_register).classes("bg-slate-700 text-white")
                    d.open()

                ui.button("＋ Register Worker", on_click=_register_worker_form).classes("bg-slate-700 text-white")

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

                    def _add_org_form() -> None:
                        with ui.dialog() as d, ui.card().classes("p-6 gap-3 w-[420px]"):
                            ui.label("Add Organization").classes("text-lg font-bold text-slate-800")
                            org_name = ui.input("Organization Name*", placeholder="e.g. District 42 Special Ed").classes("w-full")
                            role_sel = ui.select(["operator", "admin", "viewer"], value="operator", label="Initial member role").classes("w-full")
                            username_inp = ui.input("Initial member username*", placeholder="e.g. jdoe").classes("w-full")

                            def _submit_org() -> None:
                                name = org_name.value.strip()
                                username = username_inp.value.strip()
                                if not name:
                                    notify_error("Organization name is required.")
                                    return
                                if not username:
                                    notify_error("Member username is required.")
                                    return
                                org = _tenants.create_organization(name)
                                _tenants.add_member(username=username, organization_id=org.organization_id, role=role_sel.value)
                                _audit.record_event(event_type="organization_created", actor=username, payload={"org": name, "role": role_sel.value})
                                d.close()
                                notify_success(f"Organization '{name}' created.")
                                _render()

                            with ui.row().classes("justify-end gap-2 mt-2"):
                                ui.button("Cancel", on_click=d.close).props("flat").classes("text-slate-500")
                                ui.button("Create", on_click=_submit_org).classes("bg-blue-600 text-white")
                        d.open()

                    ui.button("＋ Add Organization", on_click=_add_org_form).props("flat dense").classes("text-blue-600")

                    def _add_retention_form() -> None:
                        with ui.dialog() as d, ui.card().classes("p-6 gap-3 w-[420px]"):
                            ui.label("Register Artifact for Retention").classes("text-lg font-bold text-slate-800")
                            path_inp = ui.input("Artifact Path*", placeholder="/path/to/artifact.epub").classes("w-full")
                            days_inp = ui.number("Retention Days*", value=90, min=1).classes("w-full")

                            def _submit_ret() -> None:
                                path = path_inp.value.strip()
                                if not path:
                                    notify_error("Artifact path is required.")
                                    return
                                _retention.register_artifact(path, retention_days=int(days_inp.value or 90))
                                d.close()
                                notify_success(f"Artifact registered for {int(days_inp.value)} day retention.")
                                _render()

                            with ui.row().classes("justify-end gap-2 mt-2"):
                                ui.button("Cancel", on_click=d.close).props("flat").classes("text-slate-500")
                                ui.button("Register", on_click=_submit_ret).classes("bg-indigo-600 text-white")
                        d.open()

                    ui.button("＋ Register Artifact", on_click=_add_retention_form).props("flat dense").classes("text-indigo-600")
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
