"""Workflow dependency DAG orchestration engine."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field


@dataclass(slots=True)
class WorkflowNode:
    name: str
    dependencies: set[str] = field(default_factory=set)


class WorkflowDAG:
    """Directed acyclic workflow orchestration graph."""

    def __init__(self) -> None:
        self._nodes: dict[str, WorkflowNode] = {}

    def add_workflow(
        self,
        name: str,
        *,
        dependencies: list[str] | None = None,
    ) -> None:
        self._nodes[name] = WorkflowNode(
            name=name,
            dependencies=set(dependencies or []),
        )

    def execution_order(self) -> list[str]:
        graph: dict[str, list[str]] = defaultdict(list)
        indegree: dict[str, int] = {}

        for name, node in self._nodes.items():
            indegree.setdefault(name, 0)

            for dependency in node.dependencies:
                graph[dependency].append(name)
                indegree[name] = indegree.get(name, 0) + 1

        queue = deque(
            [name for name, degree in indegree.items() if degree == 0]
        )

        ordered: list[str] = []

        while queue:
            current = queue.popleft()
            ordered.append(current)

            for neighbor in graph[current]:
                indegree[neighbor] -= 1

                if indegree[neighbor] == 0:
                    queue.append(neighbor)

        if len(ordered) != len(self._nodes):
            raise ValueError("Workflow graph contains a cycle")

        return ordered

    def visualize(self) -> list[dict]:
        return [
            {
                "workflow": node.name,
                "dependencies": sorted(node.dependencies),
            }
            for node in self._nodes.values()
        ]


__all__ = [
    "WorkflowNode",
    "WorkflowDAG",
]
