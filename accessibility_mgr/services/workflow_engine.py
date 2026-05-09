from __future__ import annotations

from models.assets import WorkflowEvent
from services.assets_service import AssetService


VALID_WORKFLOWS = {
    "braille": [
        "digitization",
        "ocr",
        "cleanup",
        "translation",
        "proofreading",
        "embossing",
        "delivery",
    ],
    "3d_print": [
        "cad_ingestion",
        "mesh_validation",
        "slicing",
        "printing",
        "qa",
        "delivery",
    ],
}


class WorkflowEngine:
    @staticmethod
    def validate_transition(workflow_type: str, stage: str) -> bool:
        stages = VALID_WORKFLOWS.get(workflow_type, [])
        return stage in stages

    @staticmethod
    def execute_stage(
        asset_id: int,
        workflow_type: str,
        stage: str,
        operator: str = "",
        notes: str = "",
    ) -> WorkflowEvent:
        if not WorkflowEngine.validate_transition(workflow_type, stage):
            raise ValueError(f"Invalid workflow stage: {stage}")

        return AssetService.add_workflow_event(
            asset_id=asset_id,
            workflow_type=workflow_type,
            stage=stage,
            operator=operator,
            notes=notes,
        )
