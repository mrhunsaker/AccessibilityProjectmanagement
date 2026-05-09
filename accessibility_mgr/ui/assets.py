"""Asset and metadata registry UI.

Provides visibility into tracked digital and physical assets, metadata events,
and workflow lineage concepts.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from nicegui import ui

DB_PATH = Path(__file__).parent.parent / "project_manager.db"


def _fetch_summary() -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    tables = {
        "file_objects": "SELECT COUNT(*) FROM file_object",
        "metadata_events": "SELECT COUNT(*) FROM metadata_event",
        "job_metadata": "SELECT COUNT(*) FROM job_metadata",
        "structural_nodes": "SELECT COUNT(*) FROM structural_map_node",
    }

    results = {}

    for key, query in tables.items():
        try:
            cur.execute(query)
            results[key] = cur.fetchone()[0]
        except sqlite3.Error:
            results[key] = 0

    conn.close()
    return results


def assets_page() -> None:
    """Render metadata and asset management overview page."""

    summary = _fetch_summary()

    ui.label("Asset Registry & Metadata Workflows").classes(
        "text-2xl font-bold"
    )

    ui.markdown(
        """
        This subsystem tracks digital and physical accessibility-production
        assets across their complete workflow lifecycle.

        The architecture is inspired by:

        - METS
        - PREMIS
        - OCR-D workspace models
        - Digital preservation systems
        """
    )

    with ui.row().classes("w-full gap-4"):
        for label, value in [
            ("Tracked Assets", summary["file_objects"]),
            ("Metadata Events", summary["metadata_events"]),
            ("Metadata Records", summary["job_metadata"]),
            ("Structural Nodes", summary["structural_nodes"]),
        ]:
            with ui.card().classes("p-4 min-w-52"):
                ui.label(label).classes("text-sm text-slate-500")
                ui.label(str(value)).classes("text-3xl font-bold")

    with ui.card().classes("w-full"):
        ui.label("Tracked Asset Types").classes("text-lg font-semibold")

        ui.markdown(
            """
            - OCR outputs
            - Corrected text
            - BRF / BRL files
            - PEF files
            - EPUB packages
            - DAISY exports
            - STL / 3MF / STEP assets
            - G-code derivatives
            - Embossed braille copies
            - Tactile graphics
            - Accessibility fabrication objects
            """
        )

    with ui.card().classes("w-full"):
        ui.label("Metadata Capture Goals").classes("text-lg font-semibold")

        with ui.grid(columns=2).classes("w-full gap-4"):
            with ui.column():
                ui.label("Descriptive Metadata").classes("font-medium")
                ui.markdown(
                    """
                    - Title
                    - Subject
                    - Language
                    - Accessibility need
                    - Requestor
                    - Keywords
                    """
                )

            with ui.column():
                ui.label("Technical Metadata").classes("font-medium")
                ui.markdown(
                    """
                    - OCR engine
                    - Translation engine
                    - Embosser settings
                    - Slicer profiles
                    - File formats
                    - Validation reports
                    """
                )

    with ui.expansion("Planned Metadata and Lineage Features"):
        ui.markdown(
            """
            - Asset version graphing
            - Parent/child derivative visualization
            - Workflow replay history
            - Preservation exports
            - Automated checksum validation
            - Operator audit trails
            - File validation pipelines
            - Metadata schema templates
            """
        )
