"""Schema governance service module.

"""
from __future__ import annotations


CONTROLLED_VOCABULARIES = {
    "language": ["en", "fr", "es", "de"],
    "accessibility_format": ["BRF", "EPUB", "PEF", "STL"],
}


class SchemaGovernanceService:
    """Service for controlled vocabulary validation and lookup."""

    @staticmethod
    def validate_controlled_value(field: str, value: str) -> bool:
        """Validate controlled value.
        
        Parameters
        ----------
        field : Any
            field parameter.
        
        value : Any
            value parameter.
        
        Returns
        -------
        Any
            Function result.
        
        """
        allowed = CONTROLLED_VOCABULARIES.get(field)

        if not allowed:
            return True

        return value in allowed

    @staticmethod
    def get_vocabularies():
        """Get vocabularies.
        
        Returns
        -------
        Any
            Function result.
        
        """
        return CONTROLLED_VOCABULARIES
