"""EPUB QA dashboard and pipeline workflow UI."""

from __future__ import annotations

from nicegui import ui

from ..services.epub_qa import EPUBQAService
from ..services.qa_persistence import QAPersistenceService
from .components import section_header


_qa_service = EPUBQAService()
_persistence = QAPersistenceService()

SAMPLE_EPUBS = [
    (1, "accessible_book.epub"),
    (2, "draft_training_manual.epub"),
    (3, "invalid_package.txt"),
]


def qa_dashboard_page(content_area: ui.element) -> None:
    """Render EPUB QA workflow dashboard."""

    content_area.clear()

    with content_area:
        section_header(
            "EPUB QA Dashboard",
            "Accessibility QA automation and pipeline orchestration",
        )

        results_box = ui.column().classes("w-full gap-4")
        pipeline_box = ui.column().classes("w-full gap-3")
        persistence_box = ui.column().classes("w-full gap-3")

        with ui.card().classes(
            "w-full p-5 rounded-xl border border-slate-200"
        ):
            ui.label("Run Accessibility QA").classes(
                "text-lg font-semibold text-slate-700 mb-3"
            )

            asset_options = {
                f"#{aid} — {name}": (aid, name)
                for aid, name in SAMPLE_EPUBS
            }

            selected = ui.select(
                list(asset_options.keys()),
                value=list(asset_options.keys())[0],
                label="EPUB Asset",
            ).classes("w-full max-w-xl")

            def _run_pipeline() -> None:
                results_box.clear()
                pipeline_box.clear()
                persistence_box.clear()

                aid, epub_name = asset_options[selected.value]

                run = _qa_service.start_pipeline(
                    pipeline_name="epub_accessibility_pipeline",
                    asset_id=aid,
                )

                _qa_service.append_log(run, "Pipeline initialized")
                _qa_service.append_log(run, "Running DAISY Ace validation")

                result = _qa_service.run_ace_check(
                    asset_id=aid,
                    epub_path=epub_name,
                )

                _qa_service.append_log(run, "Accessibility scan completed")

                _qa_service.complete_pipeline(
                    run,
                    success=result.passed,
                )

                persisted = _persistence.persist_report(
                    asset_id=aid,
                    pipeline_name=run.pipeline_name,
                    status=run.status,
                    score=result.score,
                    findings=[
                        {
                            "severity": issue.severity,
                            "code": issue.code,
                            "message": issue.message,
                        }
                        for issue in result.issues
                    ],
                )

                _persistence.persist_pipeline_run(
                    pipeline_name=run.pipeline_name,
                    asset_id=aid,
                    status=run.status,
                    logs=run.logs,
                    retry_count=run.retry_count,
                )

                artifact = _persistence.register_artifact(
                    asset_id=aid,
                    artifact_type="ace_report",
                    file_name=f"asset_{aid}_ace_report.json",
                    generated_by="EPUBQAService",
                    metadata={
                        "score": result.score,
                        "passed": result.passed,
                    },
                )

                with results_box:
                    with ui.card().classes(
                        "w-full p-4 border border-slate-200 rounded-xl"
                    ):
                        ui.label("QA Report").classes(
                            "text-base font-semibold text-slate-700"
                        )

                        status = "PASSED" if result.passed else "FAILED"
                        color = (
                            "text-green-600"
                            if result.passed
                            else "text-red-600"
                        )

                        ui.label(f"Status: {status}").classes(
                            f"text-sm font-semibold {color}"
                        )

                        ui.label(f"Engine: {result.engine}").classes(
                            "text-sm text-slate-500"
                        )

                        ui.label(f"Accessibility Score: {result.score}").classes(
                            "text-sm text-slate-500"
                        )

                        if result.issues:
                            ui.separator()
                            ui.label("Issues").classes(
                                "text-sm font-semibold text-slate-700"
                            )

                            for issue in result.issues:
                                issue_color = (
                                    "text-red-600"
                                    if issue.severity == "error"
                                    else "text-amber-600"
                                )

                                ui.label(
                                    f"[{issue.severity.upper()}] "
                                    f"{issue.code}: {issue.message}"
                                ).classes(f"text-xs {issue_color}")
                        else:
                            ui.label(
                                "No accessibility issues detected"
                            ).classes("text-sm text-green-600")

                with pipeline_box:
                    ui.label("Pipeline Execution").classes(
                        "text-sm font-semibold text-slate-700"
                    )

                    with ui.card().classes(
                        "w-full p-4 border border-slate-200 rounded-xl"
                    ):
                        ui.label(f"Pipeline: {run.pipeline_name}").classes(
                            "text-sm text-slate-600"
                        )

                        ui.label(f"Status: {run.status}").classes(
                            "text-sm text-slate-600"
                        )

                        ui.label(f"Retries: {run.retry_count}").classes(
                            "text-sm text-slate-600 mb-2"
                        )

                        ui.label("Execution Log").classes(
                            "text-xs font-semibold text-slate-700"
                        )

                        for log in run.logs:
                            ui.label(log).classes(
                                "text-xs text-slate-500 font-mono"
                            )

                        def _retry() -> None:
                            _qa_service.retry_pipeline(run)
                            ui.notify("Pipeline marked for retry")

                        ui.button(
                            "Retry Pipeline",
                            on_click=_retry,
                        ).classes("bg-amber-600 text-white mt-3")

                with persistence_box:
                    ui.label("Persisted QA Records").classes(
                        "text-sm font-semibold text-slate-700"
                    )

                    with ui.card().classes(
                        "w-full p-4 border border-slate-200 rounded-xl"
                    ):
                        ui.label(
                            f"Persisted report created at: {persisted.created_at[:19]}"
                        ).classes("text-xs text-slate-500")

                        ui.label(
                            f"Artifact: {artifact.file_name}"
                        ).classes("text-xs text-slate-500")

                        ui.label(
                            f"Artifact type: {artifact.artifact_type}"
                        ).classes("text-xs text-slate-500")

                        ui.label(
                            f"Stored reports: {len(_persistence.list_reports())}"
                        ).classes("text-xs text-slate-500")

                        ui.label(
                            f"Stored artifacts: {len(_persistence.list_artifacts())}"
                        ).classes("text-xs text-slate-500")

            ui.button(
                "Run QA Pipeline",
                on_click=_run_pipeline,
            ).classes("bg-blue-600 text-white mt-4")
