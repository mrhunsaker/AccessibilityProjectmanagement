"""Assets service module.

"""
from __future__ import annotations

from typing import Any

try:
    from ..db.database import SessionLocal
    from ..models.assets import Asset, AssetMetadata, Project, WorkflowEvent
except ModuleNotFoundError:
    SessionLocal = None
    Asset = AssetMetadata = Project = WorkflowEvent = Any


def _require_sqlalchemy() -> None:
    """Require SQLAlchemy-backed model dependencies before service use."""
    if SessionLocal is None:
        raise RuntimeError(
            "assets_service requires SQLAlchemy runtime dependencies. "
            "Install project dependencies (e.g. `uv sync`) before using this service."
        )


class AssetService:
    """Service for creating and querying legacy asset records."""

    @staticmethod
    def create_project(title: str, description: str = "") -> Project:
        """Create project.
        
        Parameters
        ----------
        title : Any
            title parameter.
        
        description : Any
            description parameter.
        
        Returns
        -------
        Any
            Function result.
        
        """
        _require_sqlalchemy()
        session = SessionLocal()

        project = Project(title=title, description=description)
        session.add(project)
        session.commit()
        session.refresh(project)
        session.close()

        return project

    @staticmethod
    def list_projects() -> list[Project]:
        """List projects.
        
        Returns
        -------
        Any
            Function result.
        
        """
        _require_sqlalchemy()
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
        """Create asset.
        
        Parameters
        ----------
        name : Any
            name parameter.
        
        asset_type : Any
            asset_type parameter.
        
        path : Any
            path parameter.
        
        project_id : Any
            project_id parameter.
        
        parent_id : Any
            parent_id parameter.
        
        Returns
        -------
        Any
            Function result.
        
        """
        _require_sqlalchemy()
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
        """List assets.
        
        Returns
        -------
        Any
            Function result.
        
        """
        _require_sqlalchemy()
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
        """Add metadata.
        
        Parameters
        ----------
        asset_id : Any
            asset_id parameter.
        
        key : Any
            key parameter.
        
        value : Any
            value parameter.
        
        metadata_group : Any
            metadata_group parameter.
        
        Returns
        -------
        Any
            Function result.
        
        """
        _require_sqlalchemy()
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
        """Add workflow event.
        
        Parameters
        ----------
        asset_id : Any
            asset_id parameter.
        
        workflow_type : Any
            workflow_type parameter.
        
        stage : Any
            stage parameter.
        
        operator : Any
            operator parameter.
        
        notes : Any
            notes parameter.
        
        Returns
        -------
        Any
            Function result.
        
        """
        _require_sqlalchemy()
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
        """Get workflow history.
        
        Parameters
        ----------
        asset_id : Any
            asset_id parameter.
        
        Returns
        -------
        Any
            Function result.
        
        """
        _require_sqlalchemy()
        session = SessionLocal()

        results = (
            session.query(WorkflowEvent)
            .filter(WorkflowEvent.asset_id == asset_id)
            .order_by(WorkflowEvent.created_at.desc())
            .all()
        )

        session.close()

        return results
