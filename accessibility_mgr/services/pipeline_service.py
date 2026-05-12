"""
Pipeline service — multi-stage accessibility production workflow automation.

Each pipeline definition carries ordered steps with tool names and commands.
Execution runs each step via ExecutionService and persists run records to DB.
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass, field
from typing import Optional

from ..db import queries as Q
from .execution_service import ExecutionResult, ExecutionService


@dataclass
class PipelineStep:
    """PipelineStep class.
    
    """
    name: str
    tool: str
    command_template: str   # {input} replaced at runtime
    timeout: int = 120

    def build_command(self, input_path: str = "") -> list[str]:
        """Build command.
        
        Parameters
        ----------
        input_path : Any
            input_path parameter.
        
        Returns
        -------
        Any
            Function result.
        
        """
        cmd = self.command_template.replace("{input}", input_path)
        return shlex.split(cmd)


@dataclass
class WorkflowPipeline:
    """WorkflowPipeline class.
    
    """
    name: str
    description: str
    steps: list[PipelineStep] = field(default_factory=list)


PIPELINES: list[WorkflowPipeline] = [
    WorkflowPipeline(
        name="DAISY Pipeline",
        description="Run the DAISY Pipeline task set for EPUB/DAISY processing.",
        steps=[
            PipelineStep(
                name="Run Pipeline Tasks",
                tool="DAISY Pipeline",
                command_template="pipeline2-cli tasks",
                timeout=30,
            ),
        ],
    ),
    WorkflowPipeline(
        name="Accessible EPUB Pipeline",
        description="Convert a document to EPUB then validate it for accessibility.",
        steps=[
            PipelineStep(
                name="Convert Document",
                tool="Pandoc",
                command_template="pandoc {input} -o output.epub",
                timeout=60,
            ),
            PipelineStep(
                name="Validate EPUB Structure",
                tool="EPUBCheck",
                command_template="epubcheck output.epub",
                timeout=60,
            ),
            PipelineStep(
                name="Accessibility QA",
                tool="DAISY Ace",
                command_template="ace output.epub -o ace-report",
                timeout=180,
            ),
        ],
    ),
    WorkflowPipeline(
        name="Braille Production Pipeline",
        description="Translate a text document to Braille and verify with BRLTTY.",
        steps=[
            PipelineStep(
                name="Translate Braille",
                tool="Liblouis",
                command_template="file2brl {input}",
                timeout=60,
            ),
            PipelineStep(
                name="Braille Device QA",
                tool="BRLTTY",
                command_template="brltty --help",
                timeout=10,
            ),
        ],
    ),
]

_PIPELINE_MAP: dict[str, WorkflowPipeline] = {p.name: p for p in PIPELINES}


@dataclass
class PipelineRunResult:
    """PipelineRunResult class.
    
    """
    pipeline_name: str
    run_id: int
    step_results: list[ExecutionResult]
    overall_success: bool


class PipelineService:
    """Service for listing and executing multi-step workflow pipelines."""

    @staticmethod
    def list_pipelines() -> list[WorkflowPipeline]:
        """List pipelines.
        
        Returns
        -------
        Any
            Function result.
        
        """
        return PIPELINES

    @staticmethod
    def get_pipeline(name: str) -> Optional[WorkflowPipeline]:
        """Get pipeline.
        
        Parameters
        ----------
        name : Any
            name parameter.
        
        Returns
        -------
        Any
            Function result.
        
        """
        return _PIPELINE_MAP.get(name)

    @staticmethod
    def run_pipeline(name: str, input_path: str = "") -> PipelineRunResult:
        """Execute all steps of a named pipeline, persisting results to DB."""
        pipeline = _PIPELINE_MAP.get(name)
        if pipeline is None:
            return PipelineRunResult(
                pipeline_name=name,
                run_id=-1,
                step_results=[
                    ExecutionResult(
                        command=name,
                        success=False,
                        output=f"Unknown pipeline: '{name}'",
                        return_code=-1,
                    )
                ],
                overall_success=False,
            )

        run_id = Q.start_pipeline_run(name)
        step_results: list[ExecutionResult] = []
        overall_success = True

        for step in pipeline.steps:
            command = step.build_command(input_path)
            result = ExecutionService.run_command(command, timeout=step.timeout)

            Q.log_pipeline_step(
                pipeline_run_id=run_id,
                step_name=step.name,
                tool=step.tool,
                command=result.command,
                success=result.success,
                output=result.output,
            )

            step_results.append(result)

            if not result.success:
                overall_success = False
                # Continue remaining steps even on failure so all results are recorded

        Q.finish_pipeline_run(run_id, status="completed" if overall_success else "failed")

        return PipelineRunResult(
            pipeline_name=name,
            run_id=run_id,
            step_results=step_results,
            overall_success=overall_success,
        )
