"""Search service module.

"""
from __future__ import annotations

from ..db.database import SessionLocal
from ..models.assets import Asset, AssetMetadata


class SearchService:
    """Service for searching legacy SQLAlchemy asset records."""

    @staticmethod
    def search_assets(query: str):
        """Search assets.
        
        Parameters
        ----------
        query : Any
            query parameter.
        
        Returns
        -------
        Any
            Function result.
        
        """
        session = SessionLocal()

        results = (
            session.query(Asset)
            .filter(Asset.name.ilike(f"%{query}%"))
            .all()
        )

        session.close()

        return results

    @staticmethod
    def search_metadata(query: str):
        """Search metadata.
        
        Parameters
        ----------
        query : Any
            query parameter.
        
        Returns
        -------
        Any
            Function result.
        
        """
        session = SessionLocal()

        results = (
            session.query(AssetMetadata)
            .filter(AssetMetadata.value.ilike(f"%{query}%"))
            .all()
        )

        session.close()

        return results
