"""Distributed worker coordination primitives."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone


@dataclass(slots=True)
class WorkerNode:
    node_id: str
    hostname: str
    status: str
    registered_at: str


class DistributedWorkerRegistry:
    """Registry for distributed orchestration workers."""

    def __init__(self) -> None:
        self._nodes: list[WorkerNode] = []

    def register_node(
        self,
        *,
        node_id: str,
        hostname: str,
    ) -> WorkerNode:
        node = WorkerNode(
            node_id=node_id,
            hostname=hostname,
            status="online",
            registered_at=datetime.now(timezone.utc).isoformat(),
        )

        self._nodes.append(node)
        return node

    def set_status(
        self,
        node_id: str,
        status: str,
    ) -> None:
        for node in self._nodes:
            if node.node_id == node_id:
                node.status = status
                return

    def list_nodes(self) -> list[dict]:
        return [asdict(node) for node in self._nodes]


__all__ = [
    "WorkerNode",
    "DistributedWorkerRegistry",
]
