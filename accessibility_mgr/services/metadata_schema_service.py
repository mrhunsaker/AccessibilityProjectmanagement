"""Metadata schema service module.

"""
from __future__ import annotations


REQUIRED_METADATA = {
    "BRF": ["title", "language"],
    "EPUB": ["title", "language", "creator"],
    "STL": ["title"],
}


class MetadataSchemaService:
    """Service for validating required metadata fields by asset type."""

    @staticmethod
    def validate(asset_type: str, metadata: dict) -> tuple[bool, list[str]]:
        """Validate.
        
        Parameters
        ----------
        asset_type : Any
            asset_type parameter.
        
        metadata : Any
            metadata parameter.
        
        Returns
        -------
        Any
            Function result.
        
        """
        errors = []

        required = REQUIRED_METADATA.get(asset_type, [])

        for field in required:
            if field not in metadata or not metadata[field]:
                errors.append(f"Missing required metadata: {field}")

        return len(errors) == 0, errors
