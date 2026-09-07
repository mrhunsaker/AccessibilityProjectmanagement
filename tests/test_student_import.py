"""Tests for bulk CSV import of student records."""

from __future__ import annotations

import csv
from pathlib import Path

from accessibility_mgr.db import queries as Q
from accessibility_mgr.services import student_import


def _write_csv(path: Path, rows: list[list[str]]) -> Path:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(student_import.TEMPLATE_HEADERS)
        writer.writerows(rows)
    return path


def test_import_students_csv_adds_and_dedupes(tmp_path) -> None:
    csv_path = _write_csv(tmp_path / "students.csv", [
        ["Smith", "Jane", "Lincoln Middle", "7", "Braille", "Tactile"],
        ["Nguyen", "Alex", "Riverview", "4", "EPUB3", ""],
        ["Smith", "Jane", "Lincoln Middle", "7", "Braille", "Duplicate row"],
    ])

    result = student_import.import_students_csv(csv_path)

    assert result.added == 2
    assert result.skipped == 1
    assert result.errors == 0
    assert len(Q.list_students()) == 2


def test_import_students_csv_skips_existing(tmp_path) -> None:
    Q.add_student("Smith", "Jane", school="Lincoln Middle")
    csv_path = _write_csv(tmp_path / "students.csv", [
        ["Smith", "Jane", "Other", "8", "", ""],
        ["Nguyen", "Alex", "Riverview", "4", "", ""],
    ])

    result = student_import.import_students_csv(csv_path)

    assert result.added == 1
    assert result.skipped == 1
    students = Q.list_students()
    assert len(students) == 2
    smith = next(s for s in students if s["last_name"] == "Smith")
    assert smith["school"] == "Lincoln Middle"


def test_preview_students_csv_reports_invalid_rows(tmp_path) -> None:
    csv_path = _write_csv(tmp_path / "students.csv", [
        ["", "Jane", "Lincoln", "7", "", ""],
        ["Nguyen", "Alex", "Riverview", "4", "", ""],
    ])

    preview = student_import.preview_students_csv(csv_path)

    assert len(preview.errors) == 1
    assert len(preview.to_add) == 1


def test_student_import_template_csv() -> None:
    content = student_import.student_import_template_csv()
    assert content.startswith(b"last_name,first_name")
