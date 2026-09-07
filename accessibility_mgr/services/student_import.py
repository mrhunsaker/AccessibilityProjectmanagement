"""Bulk-import student records from a CSV file.

Students are de-duplicated on (first name, last name) as the business key.
Re-importing an existing student is *skipped*, never overwritten. The importer
can report a preview of what would be added/skipped without writing anything,
then commit all qualifying rows in a single transaction.

This module deliberately keeps SQL in one place (mirroring the ``db`` layer's
convention) and stages no files itself; callers pass an already-staged path.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from pathlib import Path

from ..db import queries as Q

TEMPLATE_HEADERS = [
    "last_name",
    "first_name",
    "school",
    "grade",
    "preferred_formats",
    "notes",
]

TEMPLATE_ROWS = [
    ["Smith", "Jane", "Lincoln Middle School", "7", "Braille (UEB), Large Print 18pt", "Needs tactile graphics"],
    ["Nguyen", "Alex", "Riverview Elementary", "4", "EPUB3", ""],
]

_EMPTY_TOKENS = {"", "nan", "none", "null", "-", "n/a", "na"}


@dataclass
class StudentImportPreview:
    """Parsed rows awaiting confirmation, without any writes."""
    to_add: list[dict[str, str]] = field(default_factory=list)
    to_skip: list[dict[str, str]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def total_rows(self) -> int:
        return len(self.to_add) + len(self.to_skip) + len(self.errors)


@dataclass
class StudentImportResult:
    """Outcome after importing a CSV file."""
    added: int = 0
    skipped: int = 0
    errors: int = 0
    details: list[str] = field(default_factory=list)


def student_import_template_csv() -> bytes:
    """Return the CSV template as UTF-8 bytes for browser download."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(TEMPLATE_HEADERS)
    writer.writerows(TEMPLATE_ROWS)
    return buf.getvalue().encode("utf-8")


def _clean(value: object) -> str:
    """Normalise a CSV cell to a trimmed string, mapping empties to ''."""
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in _EMPTY_TOKENS:
        return ""
    return text


def _row_from_csv(row: dict[str, str]) -> dict[str, str]:
    """Extract/clean the known student fields from a parsed CSV row."""
    return {
        "last_name": _clean(row.get("last_name")),
        "first_name": _clean(row.get("first_name")),
        "school": _clean(row.get("school")),
        "grade": _clean(row.get("grade")),
        "preferred_formats": _clean(row.get("preferred_formats")),
        "notes": _clean(row.get("notes")),
    }


def _student_business_key(last: str, first: str) -> str:
    return f"{last.strip().casefold()}|{first.strip().casefold()}"


def _existing_keys() -> set[str]:
    """Return the set of business keys for all persisted students."""
    with Q.get_conn() as conn:
        rows = conn.execute(
            "SELECT last_name, first_name FROM student"
        ).fetchall()
    return {
        _student_business_key(row[0], row[1])
        for row in rows
    }


def _read_rows(path: Path) -> list[dict[str, str]]:
    """Parse a CSV file into cleaned per-student dicts (header-driven)."""
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return [_row_from_csv(row) for row in csv.DictReader(fh)]


def _dedupe_and_bucket(
    rows: list[dict[str, str]],
    existing: set[str],
) -> StudentImportPreview:
    """Bucket rows into to_add/to_skip plus shape errors.

    De-duplicates both within the file (first occurrence wins) and against the
    existing database. Rows missing a first or last name are reported as errors.
    """
    preview = StudentImportPreview()
    seen: set[str] = set()

    for i, row in enumerate(rows, start=1):
        last = row["last_name"]
        first = row["first_name"]
        if not last or not first:
            preview.errors.append(f"Row {i}: requires both first_name and last_name (got '{first}' / '{last}')")
            continue
        key = _student_business_key(last, first)
        if key in seen or key in existing:
            preview.to_skip.append(row)
            continue
        seen.add(key)
        preview.to_add.append(row)

    return preview


def preview_students_csv(path: str | Path) -> StudentImportPreview:
    """Parse and bucket a CSV into add/skip/error lists without writing."""
    return _dedupe_and_bucket(
        _read_rows(Path(path)),
        _existing_keys(),
    )


def import_students_csv(path: str | Path) -> StudentImportResult:
    """Import qualifying rows from *path* into the database in one transaction.

    Only rows flagged for addition in a preview are inserted. Duplicate and
    invalid rows are skipped (never overwritten). Returns outcome counts.
    """
    preview = _dedupe_and_bucket(
        _read_rows(Path(path)),
        _existing_keys(),
    )

    result = StudentImportResult(skipped=len(preview.to_skip), errors=len(preview.errors))

    if not preview.to_add:
        return result

    with Q.get_conn() as conn:
        conn.executemany(
            "INSERT INTO student (last_name, first_name, school, grade, preferred_formats, notes) "
            "VALUES (:last_name, :first_name, :school, :grade, :preferred_formats, :notes)",
            preview.to_add,
        )

    result.added = len(preview.to_add)
    for row in preview.to_add:
        result.details.append(
            f"Added {row['last_name']}, {row['first_name']}"
        )
    return result
