"""Metadata option catalog for UI forms.

Defaults live in this file and can be overridden/extended from Admin Settings,
where metadata keys are persisted in ``material_category`` sections.
"""

from __future__ import annotations

METADATA_CATEGORY_SECTIONS = {
    "Dublin Core": "metadata_dublin_core",
    "eBraille Profile": "metadata_ebraille_profile",
    "METS / PREMIS": "metadata_mets_premis",
}

# Dublin Core (15-element set)
DUBLIN_CORE_KEYS = [
    "dc:title",
    "dc:creator",
    "dc:subject",
    "dc:description",
    "dc:publisher",
    "dc:contributor",
    "dc:date",
    "dc:type",
    "dc:format",
    "dc:identifier",
    "dc:source",
    "dc:language",
    "dc:relation",
    "dc:coverage",
    "dc:rights",
]

# Light-gray examples shown under each DC field.
# Example source: Project Gutenberg ebook 1342 (Pride and Prejudice).
DUBLIN_CORE_EXAMPLES = {
    "dc:title": "Example: Pride and Prejudice",
    "dc:creator": "Example: Austen, Jane",
    "dc:subject": "Example: Courtship -- Fiction",
    "dc:description": "Example: A Regency-era novel about Elizabeth Bennet and Mr. Darcy.",
    "dc:publisher": "Example: Project Gutenberg",
    "dc:contributor": "Example: Illustrated by Hugh Thomson",
    "dc:date": "Example: 1813-01-28",
    "dc:type": "Example: Text",
    "dc:format": "Example: text/plain; charset=utf-8",
    "dc:identifier": "Example: gutenberg:1342",
    "dc:source": "Example: https://www.gutenberg.org/ebooks/1342",
    "dc:language": "Example: en",
    "dc:relation": "Example: Gutenberg Bookshelf: Best Books Ever Listings",
    "dc:coverage": "Example: England -- 19th century",
    "dc:rights": "Example: Public domain in the United States",
}

# Common eBraille and accessibility-production profile fields.
EBRAILLE_PROFILE_KEYS = [
    "grade_level",
    "subject_area",
    "isbn",
    "oclc_number",
    "series",
    "volume",
    "edition",
    "transcriber",
    "proofreader",
    "embosser",
    "emboss_date",
    "braille_code",
    "contracted_status",
    "nemeth_used",
    "tactile_graphics_present",
    "reading_level",
]

# METS/PREMIS-aligned operational fields.
METS_PREMIS_KEYS = [
    "mets:file_group",
    "mets:div_type",
    "mets:struct_order",
    "mets:amdsec_id",
    "premis:event_type",
    "premis:event_datetime",
    "premis:event_outcome",
    "premis:agent",
    "premis:object_identifier",
    "premis:rights_basis",
    "premis:significant_properties",
    "premis:storage_location",
]

DEFAULT_ALLOWED_METADATA_KEYS = DUBLIN_CORE_KEYS + EBRAILLE_PROFILE_KEYS + METS_PREMIS_KEYS
DEFAULT_NON_DC_ALLOWED_KEYS = EBRAILLE_PROFILE_KEYS + METS_PREMIS_KEYS

DEFAULT_OPTION_GROUPS = {
    "Dublin Core": DUBLIN_CORE_KEYS,
    "eBraille Profile": EBRAILLE_PROFILE_KEYS,
    "METS / PREMIS": METS_PREMIS_KEYS,
}


def _load_runtime_option_groups() -> dict[str, list[str]]:
    """Load metadata options from DB-backed material categories when available."""
    try:
        from ..db import queries as Q
    except Exception:
        return DEFAULT_OPTION_GROUPS

    groups: dict[str, list[str]] = {}
    for label, section in METADATA_CATEGORY_SECTIONS.items():
        try:
            rows = Q.list_material_categories(section=section, active_only=True)
        except Exception:
            rows = []
        loaded = [r.get("value", "") for r in rows if r.get("value")]
        groups[label] = loaded or list(DEFAULT_OPTION_GROUPS.get(label, []))

    return groups


def get_option_groups() -> dict[str, list[str]]:
    """Get option groups.
    
    Returns
    -------
    Any
        Function result.
    
    """
    return _load_runtime_option_groups()


def get_dublin_core_keys() -> list[str]:
    """Get dublin core keys.
    
    Returns
    -------
    Any
        Function result.
    
    """
    return list(get_option_groups().get("Dublin Core", []))


def get_non_dc_allowed_keys() -> list[str]:
    """Get non dc allowed keys.
    
    Returns
    -------
    Any
        Function result.
    
    """
    groups = get_option_groups()
    return list(groups.get("eBraille Profile", [])) + list(groups.get("METS / PREMIS", []))


def get_allowed_metadata_keys() -> list[str]:
    """Get allowed metadata keys.
    
    Returns
    -------
    Any
        Function result.
    
    """
    groups = get_option_groups()
    return list(groups.get("Dublin Core", [])) + get_non_dc_allowed_keys()


def get_dublin_core_examples() -> dict[str, str]:
    """Return examples keyed by current DC keys (blank when no built-in example exists)."""
    return {k: DUBLIN_CORE_EXAMPLES.get(k, "") for k in get_dublin_core_keys()}
