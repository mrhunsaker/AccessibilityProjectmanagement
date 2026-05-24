"""Metadata governance and validation services.

This module centralizes metadata normalization, controlled vocabulary
validation, and accessibility metadata checks for EPUB-oriented workflows.
"""

from __future__ import annotations

from dataclasses import dataclass, field


DC_REQUIRED_FIELDS = {
    "title",
    "creator",
    "language",
    "identifier",
}

SUPPORTED_LANGUAGES = {
    "en",
    "es",
    "fr",
    "de",
    "it",
    "ja",
    "zh",
}

ACCESS_MODE_VALUES = {
    "textual",
    "visual",
    "auditory",
    "tactile",
}

ACCESS_HAZARD_VALUES = {
    "none",
    "flashing",
    "motionSimulation",
    "sound",
}


@dataclass(slots=True)
class ValidationIssue:
    field_name: str
    severity: str
    message: str
    suggested_value: str | None = None


@dataclass(slots=True)
class ValidationResult:
    valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)


class MetadataValidationService:
    """Validate metadata against governance and accessibility rules."""

    def validate_dublin_core(
        self,
        metadata: dict,
    ) -> ValidationResult:
        issues: list[ValidationIssue] = []

        for field_name in sorted(DC_REQUIRED_FIELDS):
            value = metadata.get(field_name)

            if value:
                continue

            issues.append(
                ValidationIssue(
                    field_name=field_name,
                    severity="error",
                    message=f"Required Dublin Core field missing: {field_name}",
                )
            )

        language = metadata.get("language")

        if language and language not in SUPPORTED_LANGUAGES:
            issues.append(
                ValidationIssue(
                    field_name="language",
                    severity="warning",
                    message="Language code is not in approved vocabulary",
                    suggested_value="en",
                )
            )

        return ValidationResult(valid=not issues, issues=issues)

    def validate_epub_accessibility(
        self,
        metadata: dict,
    ) -> ValidationResult:
        issues: list[ValidationIssue] = []

        access_mode = metadata.get("schema:accessMode")

        if access_mode and access_mode not in ACCESS_MODE_VALUES:
            issues.append(
                ValidationIssue(
                    field_name="schema:accessMode",
                    severity="error",
                    message="Invalid accessibility accessMode value",
                    suggested_value="textual",
                )
            )

        access_hazard = metadata.get("schema:accessHazard")

        if access_hazard and access_hazard not in ACCESS_HAZARD_VALUES:
            issues.append(
                ValidationIssue(
                    field_name="schema:accessHazard",
                    severity="error",
                    message="Invalid accessibility hazard declaration",
                    suggested_value="none",
                )
            )

        if not metadata.get("schema:accessibilitySummary"):
            issues.append(
                ValidationIssue(
                    field_name="schema:accessibilitySummary",
                    severity="warning",
                    message="Accessibility summary should be provided",
                )
            )

        return ValidationResult(valid=not issues, issues=issues)

    def validate_all(self, metadata: dict) -> ValidationResult:
        dc_result = self.validate_dublin_core(metadata)
        epub_result = self.validate_epub_accessibility(metadata)

        issues = dc_result.issues + epub_result.issues

        has_errors = any(issue.severity == "error" for issue in issues)

        return ValidationResult(
            valid=not has_errors,
            issues=issues,
        )


__all__ = [
    "MetadataValidationService",
    "ValidationIssue",
    "ValidationResult",
]
