from __future__ import annotations


CONTROLLED_VOCABULARIES = {
    "language": ["en", "fr", "es", "de"],
    "accessibility_format": ["BRF", "EPUB", "PEF", "STL"],
}


class SchemaGovernanceService:
    @staticmethod
    def validate_controlled_value(field: str, value: str) -> bool:
        allowed = CONTROLLED_VOCABULARIES.get(field)

        if not allowed:
            return True

        return value in allowed

    @staticmethod
    def get_vocabularies():
        return CONTROLLED_VOCABULARIES
