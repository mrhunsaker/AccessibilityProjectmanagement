from __future__ import annotations

from db.database import SessionLocal
from models.assets import Asset, AssetMetadata


class SearchService:
    @staticmethod
    def search_assets(query: str):
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
        session = SessionLocal()

        results = (
            session.query(AssetMetadata)
            .filter(AssetMetadata.value.ilike(f"%{query}%"))
            .all()
        )

        session.close()

        return results
