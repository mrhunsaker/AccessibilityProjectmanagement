"""Operations analytics dashboard."""

from __future__ import annotations

from nicegui import ui

from ..services.analytics import AnalyticsService
from .components import section_header


_analytics = AnalyticsService()

# Seed representative KPI data.
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



def operations_dashboard_page(content_area: ui.element) -> None:
    """Render operational analytics dashboard."""

    content_area.clear()

    summary = _analytics.summarize()

    with content_area:
        section_header(
            "Operations Dashboard",
            "Operational analytics, QA KPIs, and governance metrics",
        )

        with ui.grid(columns=3).classes("w-full gap-4 mb-6"):
            with ui.card().classes(
                "p-5 rounded-xl border border-slate-200"
            ):
                ui.label("Tracked Metrics").classes(
                    "text-sm text-slate-500"
                )
                ui.label(str(summary["total_metrics"])).classes(
                    "text-3xl font-bold text-slate-700"
                )

            with ui.card().classes(
                "p-5 rounded-xl border border-slate-200"
            ):
                ui.label("Average KPI Score").classes(
                    "text-sm text-slate-500"
                )
                ui.label(str(summary["average_score"])).classes(
                    "text-3xl font-bold text-green-600"
                )

            with ui.card().classes(
                "p-5 rounded-xl border border-slate-200"
            ):
                ui.label("Metric Categories").classes(
                    "text-sm text-slate-500"
                )
                ui.label(str(len(summary["categories"]))).classes(
                    "text-3xl font-bold text-blue-600"
                )

        with ui.card().classes(
            "w-full p-5 rounded-xl border border-slate-200 mb-6"
        ):
            ui.label("Category Distribution").classes(
                "text-base font-semibold text-slate-700 mb-3"
            )

            for category, count in summary["categories"].items():
                with ui.row().classes(
                    "items-center justify-between border-b border-slate-100 py-2"
                ):
                    ui.label(category).classes(
                        "text-sm text-slate-700 font-medium"
                    )
                    ui.badge(str(count)).classes(
                        "bg-slate-100 text-slate-700"
                    )

        with ui.card().classes(
            "w-full p-5 rounded-xl border border-slate-200"
        ):
            ui.label("Metric Timeline").classes(
                "text-base font-semibold text-slate-700 mb-3"
            )

            for metric in _analytics.list_metrics():
                with ui.row().classes(
                    "items-start justify-between border-b border-slate-100 py-2 gap-3"
                ):
                    with ui.column().classes("gap-0 flex-1"):
                        ui.label(metric["metric_name"]).classes(
                            "text-sm font-medium text-slate-700"
                        )

                        ui.label(
                            f"Category: {metric['category']}"
                        ).classes("text-xs text-slate-500")

                    ui.label(str(metric["metric_value"])).classes(
                        "text-sm font-bold text-green-600"
                    )

                    ui.label(metric["recorded_at"][:19]).classes(
                        "text-xs text-slate-400 font-mono"
                    )
