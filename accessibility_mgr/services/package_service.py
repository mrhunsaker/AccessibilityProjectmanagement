from __future__ import annotations

import json
from pathlib import Path

from services.assets_service import AssetService


class PackageService:
    @staticmethod
    def export_package(output_path: str = "exports"):
        assets = AssetService.list_assets()

        export_dir = Path(output_path)
        export_dir.mkdir(exist_ok=True)

        manifest = []

        for asset in assets:
            manifest.append(
                {
                    "id": asset.id,
                    "name": asset.name,
                    "type": asset.asset_type,
                    "path": asset.path,
                    "parent_id": asset.parent_id,
                }
            )

        package_path = export_dir / "preservation_manifest.json"
        package_path.write_text(json.dumps(manifest, indent=2))

        return str(package_path)
