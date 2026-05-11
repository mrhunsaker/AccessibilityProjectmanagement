"""Automation integration catalogue for accessibility production tooling."""

from __future__ import annotations


AUTOMATION_TOOLS = {
    "Marker PDF": "Datalab document remediation and PDF extraction",
    "Liblouis": "Braille translation engine",
    "Pandoc": "Document conversion pipeline",
    "Calibre": "EPUB and eBook conversion",
    "OrcaSlicer": "3D printing slicing workflows",
    "BRLTTY": "Braille terminal and device tooling",
    "APH Braille Tools": "APH accessibility production utilities",
}


class AutomationService:
    @staticmethod
    def list_integrations():
        return AUTOMATION_TOOLS
