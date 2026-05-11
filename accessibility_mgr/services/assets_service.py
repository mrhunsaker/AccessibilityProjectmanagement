from __future__ import annotations

from ..db.database import SessionLocal
from ..models.assets import Asset, AssetMetadata, Project, WorkflowEvent


class AssetService:
    @staticmethod
    def create_project(title: str, description: str = "") -> Project:
        session = SessionLocal()

        project = Project(title=title, description=description)
        session.add(project)
        session.commit()
        session.refresh(project)
        session.close()

        return project

    @staticmethod
    def list_projects() -> list[Project]:
        session = SessionLocal()
        results = session.query(Project).all()
        session.close()
        return results

    @staticmethod
    def create_asset(
        name: str,
        asset_type: str,
        path: str = "",
        project_id: int | None = None,
        parent_id: int | None = None,
    ) -> Asset:
        session = SessionLocal()

        asset = Asset(
            name=name,
            asset_type=asset_type,
            path=path,
            project_id=project_id,
            parent_id=parent_id,
        )

        session.add(asset)
        session.commit()
        session.refresh(asset)
        session.close()

        return asset

    @staticmethod
    def list_assets() -> list[Asset]:
        session = SessionLocal()
        results = session.query(Asset).all()
        session.close()
        return results

    @staticmethod
    def add_metadata(
        asset_id: int,
        key: str,
        value: str,
        metadata_group: str = "general",
    ) -> AssetMetadata:
        session = SessionLocal()

        record = AssetMetadata(
            asset_id=asset_id,
            key=key,
            value=value,
            metadata_group=metadata_group,
        )

        session.add(record)
        session.commit()
        session.refresh(record)
        session.close()

        return record

    @staticmethod
    def add_workflow_event(
        asset_id: int | None,
        workflow_type: str,
        stage: str,
        operator: str = "",
        notes: str = "",
    ) -> WorkflowEvent:
        session = SessionLocal()

        event = WorkflowEvent(
            asset_id=asset_id,
            workflow_type=workflow_type,
            stage=stage,
            operator=operator,
            notes=notes,
            completed=True,
        )

        session.add(event)
        session.commit()
        session.refresh(event)
        session.close()

        return event

    @staticmethod
    def get_workflow_history(asset_id: int) -> list[WorkflowEvent]:
        session = SessionLocal()

        results = (
            session.query(WorkflowEvent)
            .filter(WorkflowEvent.asset_id == asset_id)
            .order_by(WorkflowEvent.created_at.desc())
            .all()
        )

        session.close()

        return results
