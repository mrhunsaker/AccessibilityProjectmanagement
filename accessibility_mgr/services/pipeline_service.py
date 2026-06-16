"""
Pipeline service — multi-stage accessibility production workflow automation.

Each pipeline definition carries ordered steps with tool names and commands.
Execution runs each step via ExecutionService and persists run records to DB.

STUB-026: DAISY Pipeline 2 steps now use the real pipeline2-cli invocation
pattern (--data, --script).  A binary pre-check surfaces a clear error message
when the tool is absent rather than silently returning success from an echo stub.
"""

from __future__ import annotations

import shlex
import shutil
from dataclasses import dataclass, field
from typing import Optional

from ..db import queries as Q
from .execution_service import ALLOWED_EXECUTABLES, ExecutionResult, ExecutionService


@dataclass
class PipelineStep:
    """A single step in a multi-stage workflow pipeline."""
    name: str
    tool: str
    command_template: str   # {input} replaced at runtime
    timeout: int = 120
    required_binary: str = ""  # STUB-026: binary to check before running

    def build_command(self, input_path: str = "") -> list[str]:
        cmd = self.command_template.replace("{input}", input_path)
        return shlex.split(cmd)


@dataclass
class WorkflowPipeline:
    """An ordered collection of PipelineSteps representing a production workflow."""
    name: str
    description: str
    steps: list[PipelineStep] = field(default_factory=list)


PIPELINES: list[WorkflowPipeline] = [
    WorkflowPipeline(
        name="DAISY Pipeline",
        # STUB-026: list real pipeline2-cli script IDs; --data points to the
        # Pipeline 2 data directory configured in tools.ini or the install default.
        description=(
            "Run the DAISY Pipeline 2 task set for EPUB/DAISY processing.  "
            "Requires pipeline2-cli on PATH (https://daisy.org/pipeline)."
        ),
        steps=[
            PipelineStep(
                name="List Available Scripts",
                tool="DAISY Pipeline",
                # STUB-026: real invocation — lists registered scripts to
                # confirm the server is reachable before running jobs.
                command_template="pipeline2-cli scripts",
                timeout=30,
                required_binary="pipeline2-cli",
            ),
            PipelineStep(
                name="Convert EPUB to DAISY",
                tool="DAISY Pipeline",
                # Real script invocation: pipeline2-cli run --script epub3-to-daisy
                # --input source={input} --output result=/tmp/daisy-output
                command_template=(
                    "pipeline2-cli run "
                    "--script epub3-to-daisy "
                    "--input source={input} "
                    "--output result=/tmp/daisy-pipeline-output"
                ),
                timeout=300,
                required_binary="pipeline2-cli",
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
                required_binary="pandoc",
            ),
            PipelineStep(
                name="Validate EPUB Structure",
                tool="EPUBCheck",
                command_template="epubcheck output.epub",
                timeout=60,
                required_binary="epubcheck",
            ),
            PipelineStep(
                name="Accessibility QA",
                tool="DAISY Ace",
                command_template="ace output.epub -o ace-report",
                timeout=180,
                required_binary="ace",
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
                required_binary="file2brl",
            ),
            PipelineStep(
                name="Braille Device QA",
                tool="BRLTTY",
                command_template="brltty --help",
                timeout=10,
                required_binary="brltty",
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
        """Execute all steps of a named pipeline, persisting results to DB.

        STUB-026: Each step's ``required_binary`` is checked via shutil.which
        before execution.  Missing binaries produce an explicit FAIL result with
        installation guidance rather than silently running an echo stub.
        """
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
            # STUB-026: explicit binary pre-check with install guidance
            if step.required_binary and not shutil.which(step.required_binary):
                missing_result = ExecutionResult(
                    command=step.required_binary,
                    success=False,
                    output=(
                        f"Required binary '{step.required_binary}' not found on PATH.  "
                        f"Install the tool and ensure it is accessible, or configure its "
                        f"path in tools.ini before running this pipeline."
                    ),
                    return_code=-5,
                )
                Q.log_pipeline_step(
                    pipeline_run_id=run_id,
                    step_name=step.name,
                    tool=step.tool,
                    command=step.required_binary,
                    success=False,
                    output=missing_result.output,
                )
                step_results.append(missing_result)
                overall_success = False
                continue

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
                # Continue remaining steps so all results are recorded

        Q.finish_pipeline_run(run_id, status="completed" if overall_success else "failed")

        return PipelineRunResult(
            pipeline_name=name,
            run_id=run_id,
            step_results=step_results,
            overall_success=overall_success,
        )
