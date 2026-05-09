from __future__ import annotations

import hashlib
from pathlib import Path

from services.assets_service import AssetService


class FileIngestionService:
    @staticmethod
    def calculate_checksum(path: str) -> str:
        sha256 = hashlib.sha256()

        with open(path, "rb") as file_handle:
            while chunk := file_handle.read(8192):
                sha256.update(chunk)

        return sha256.hexdigest()

    @staticmethod
    def ingest_file(
        file_path: str,
        asset_type: str,
    ):
        path = Path(file_path)

        checksum = FileIngestionService.calculate_checksum(file_path)

        asset = AssetService.create_asset(
            name=path.name,
            asset_type=asset_type,
            path=str(path),
        )

        AssetService.add_metadata(
            asset.id,
            "checksum",
            checksum,
            "preservation",
        )

        AssetService.add_metadata(
            asset.id,
            "file_size",
            str(path.stat().st_size),
            "technical",
        )

        return asset
