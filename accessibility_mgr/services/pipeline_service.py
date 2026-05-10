from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PipelineStep:
    name: str
    tool: str
    command: str


@dataclass
class WorkflowPipeline:
    name: str
    steps: list[PipelineStep] = field(default_factory=list)


PIPELINES = [
    WorkflowPipeline(
        name="Accessible EPUB Pipeline",
        steps=[
            PipelineStep(
                name="Convert Document",
                tool="Pandoc",
                command="pandoc input.docx -o output.epub",
            ),
            PipelineStep(
                name="Validate EPUB",
                tool="EPUBCheck",
                command="epubcheck output.epub",
            ),
            PipelineStep(
                name="Accessibility QA",
                tool="DAISY Ace",
                command="ace output.epub -o reports/",
            ),
        ],
    ),
    WorkflowPipeline(
        name="Braille Production Pipeline",
        steps=[
            PipelineStep(
                name="Translate Braille",
                tool="Liblouis",
                command="file2brl input.txt",
            ),
            PipelineStep(
                name="Braille QA",
                tool="BRLTTY",
                command="brltty -h",
            ),
        ],
    ),
]


class PipelineService:
    @staticmethod
    def list_pipelines() -> list[WorkflowPipeline]:
        return PIPELINES
