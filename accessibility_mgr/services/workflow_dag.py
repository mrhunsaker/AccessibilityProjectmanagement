"""Dependency-aware workflow DAG orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass(slots=True)
class WorkflowNode:
    workflow_name: str
    dependencies: list[str] = field(default_factory=list)
    retry_limit: int = 3
    status: str = "pending"


class WorkflowDAGService:
    """Dependency-aware orchestration engine."""

    def __init__(self) -> None:
        self._nodes: dict[str, WorkflowNode] = {}

    def register_workflow(
        self,
        *,
        workflow_name: str,
        dependencies: list[str] | None = None,
        retry_limit: int = 3,
    ) -> WorkflowNode:
        node = WorkflowNode(
            workflow_name=workflow_name,
            dependencies=dependencies or [],
            retry_limit=retry_limit,
        )

        self._nodes[workflow_name] = node
        return node

    def executable_workflows(self) -> list[dict[str, Any]]:
        executable = []

        for node in self._nodes.values():
            if node.status != "pending":
                continue

            blocked = False

            for dependency in node.dependencies:
                dep = self._nodes.get(dependency)

                if dep and dep.status != "completed":
                    blocked = True
                    break

            if not blocked:
                executable.append(asdict(node))

        return executable

    def complete(self, workflow_name: str) -> None:
        if workflow_name in self._nodes:
            self._nodes[workflow_name].status = "completed"

    def fail(self, workflow_name: str) -> None:
        if workflow_name in self._nodes:
            self._nodes[workflow_name].status = "failed"

    def topology(self) -> list[dict[str, Any]]:
        return [
            asdict(node)
            for node in self._nodes.values()
        ]


__all__ = [
    "WorkflowDAGService",
    "WorkflowNode",
]
