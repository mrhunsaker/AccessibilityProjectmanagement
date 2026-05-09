from __future__ import annotations


REQUIRED_METADATA = {
    "BRF": ["title", "language"],
    "EPUB": ["title", "language", "creator"],
    "STL": ["title"],
}


class MetadataSchemaService:
    @staticmethod
    def validate(asset_type: str, metadata: dict) -> tuple[bool, list[str]]:
        errors = []

        required = REQUIRED_METADATA.get(asset_type, [])

        for field in required:
            if field not in metadata or not metadata[field]:
                errors.append(f"Missing required metadata: {field}")

        return len(errors) == 0, errors
