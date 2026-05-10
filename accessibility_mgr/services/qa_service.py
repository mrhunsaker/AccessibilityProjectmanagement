from __future__ import annotations

from dataclasses import dataclass


@dataclass
class QATool:
    name: str
    domain: str
    description: str
    command_hint: str


QA_TOOLS = [
    QATool(
        name="DAISY Ace",
        domain="EPUB Accessibility",
        description="WCAG and EPUB accessibility validation",
        command_hint="ace input.epub -o reports/",
    ),
    QATool(
        name="EPUBCheck",
        domain="EPUB Validation",
        description="Structural EPUB conformance validation",
        command_hint="epubcheck input.epub",
    ),
    QATool(
        name="DAISY Pipeline",
        domain="DAISY Processing",
        description="DAISY conversion and accessibility workflows",
        command_hint="pipeline2-cli tasks",
    ),
    QATool(
        name="Liblouis",
        domain="Braille QA",
        description="Braille translation verification",
        command_hint="file2brl input.txt",
    ),
    QATool(
        name="BRLTTY",
        domain="Braille Device QA",
        description="Braille hardware interaction validation",
        command_hint="brltty -h",
    ),
    QATool(
        name="Pandoc",
        domain="Document QA",
        description="Document conversion verification",
        command_hint="pandoc input.docx -o output.html",
    ),
    QATool(
        name="ANZAGG Validation",
        domain="3D Accessibility",
        description="Tactile and accessible 3D print review workflows",
        command_hint="manual_review_required",
    ),
]


class QAService:
    @staticmethod
    def list_tools() -> list[QATool]:
        return QA_TOOLS
