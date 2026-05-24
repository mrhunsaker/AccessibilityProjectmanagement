{
  "project": "Accessibility Project Manager",
  "spec_version": "1.0",
  "generated_from": "AUDIT.md",
  "fixes": [
    {
      "id": "FIX-001",
      "priority": 1,
      "title": "Log audit events for all edit operations",
      "requirement": "Auditability",
      "status": "open",
      "depends_on": [],
      "description": "update_braille_job, update_lp_job, update_tactile_job, and update_print_job execute SQL UPDATEs with no corresponding log_event call. Any field change — requester, due date, priority, title — leaves no audit trace.",
      "files_to_modify": [
        "accessibility_mgr/db/queries.py"
      ],
      "changes": [
        {
          "function": "update_braille_job",
          "action": "modify",
          "description": "Fetch current record before update, call log_event after update with changed field names and previous values serialized into extra_metadata.",
          "insert_before_return": "log_event('braille', row_id, 'FIELD_UPDATE', 'SUCCESS', agent='system', detail=f'Updated fields: {list(fields.keys())}', extra_metadata={'changed_fields': list(fields.keys()), 'previous_values': {k: old.get(k) for k in fields if old}} )",
          "prerequisite_call": "old = get_braille_job(row_id)"
        },
        {
          "function": "update_lp_job",
          "action": "modify",
          "description": "Same pattern as update_braille_job using get_lp_job and job_type 'lp_ebraille'.",
          "insert_before_return": "log_event('lp_ebraille', row_id, 'FIELD_UPDATE', 'SUCCESS', agent='system', detail=f'Updated fields: {list(fields.keys())}', extra_metadata={'changed_fields': list(fields.keys()), 'previous_values': {k: old.get(k) for k in fields if old}} )",
          "prerequisite_call": "old = get_lp_job(row_id)"
        },
        {
          "function": "update_tactile_job",
          "action": "modify",
          "description": "Same pattern using get_tactile_job and job_type 'tactile'.",
          "insert_before_return": "log_event('tactile', row_id, 'FIELD_UPDATE', 'SUCCESS', agent='system', detail=f'Updated fields: {list(fields.keys())}', extra_metadata={'changed_fields': list(fields.keys()), 'previous_values': {k: old.get(k) for k in fields if old}} )",
          "prerequisite_call": "old = get_tactile_job(row_id)"
        },
        {
          "function": "update_print_job",
          "action": "modify",
          "description": "Same pattern. Fetch print job record first. Note: print_job has no dedicated get function — add get_print_job or inline a SELECT by id.",
          "new_helper_function": "get_print_job(row_id: int) -> Optional[dict] — SELECT * FROM print_job WHERE id = ?",
          "insert_before_return": "log_event('print', row_id, 'FIELD_UPDATE', 'SUCCESS', agent='system', detail=f'Updated fields: {list(fields.keys())}', extra_metadata={'changed_fields': list(fields.keys()), 'previous_values': {k: old.get(k) for k in fields if old}} )",
          "prerequisite_call": "old = get_print_job(row_id)"
        }
      ]
    },
    {
      "id": "FIX-002",
      "priority": 2,
      "title": "Log audit events before all delete operations",
      "requirement": "Auditability",
      "status": "open",
      "depends_on": ["FIX-001"],
      "description": "delete_braille_job, delete_lp_job, delete_tactile_job, and delete_print_job issue a bare DELETE with no prior event record. Jobs can be permanently removed with zero trace.",
      "files_to_modify": [
        "accessibility_mgr/db/queries.py"
      ],
      "changes": [
        {
          "function": "delete_braille_job",
          "action": "modify",
          "description": "Fetch job record, log DELETE event capturing title and key fields, then execute DELETE.",
          "pattern": "fetch -> log_event -> DELETE",
          "event_type": "DELETE",
          "event_outcome": "SUCCESS",
          "extra_metadata_fields": ["title", "braille_type", "requester", "priority", "created_at"]
        },
        {
          "function": "delete_lp_job",
          "action": "modify",
          "description": "Same pattern. Capture title, job_type, requester, priority.",
          "event_type": "DELETE",
          "extra_metadata_fields": ["title", "job_type", "requester", "priority", "created_at"]
        },
        {
          "function": "delete_tactile_job",
          "action": "modify",
          "description": "Same pattern. Capture title, tactile_type, requester, priority.",
          "event_type": "DELETE",
          "extra_metadata_fields": ["title", "tactile_type", "requester", "priority", "created_at"]
        },
        {
          "function": "delete_print_job",
          "action": "modify",
          "description": "Same pattern. Capture object_name, printer_id, filament_used_g, successful.",
          "event_type": "DELETE",
          "extra_metadata_fields": ["object_name", "printer_id", "filament_used_g", "successful", "printed_at"]
        },
        {
          "function": "delete_file_object",
          "action": "modify",
          "description": "Already fetches the row before deleting. Add log_event call between fetch and DELETE capturing original_name, stored_path, checksum_sha256, file_use.",
          "event_type": "DELETE",
          "job_type_value": "file",
          "note": "job_type='file' and job_id=file_id since file_object is not tied to a single job"
        }
      ]
    },
    {
      "id": "FIX-003",
      "priority": 3,
      "title": "Log audit events when metadata is saved",
      "requirement": "Auditability",
      "status": "open",
      "depends_on": [],
      "description": "set_job_metadata performs an upsert with no log_event call. MetadataAuditService in metadata_editor.py captures changes but stores them in a Python list that is lost on restart. Metadata edits are currently invisible in the audit trail.",
      "files_to_modify": [
        "accessibility_mgr/ui/braille_jobs.py",
        "accessibility_mgr/ui/lp_ebraille.py",
        "accessibility_mgr/ui/print_jobs.py",
        "accessibility_mgr/ui/tactile_graphics.py",
        "accessibility_mgr/ui/metadata_editor.py"
      ],
      "changes": [
        {
          "file": "accessibility_mgr/ui/braille_jobs.py",
          "function": "_metadata_dialog._save_all",
          "action": "modify",
          "description": "After the save loop completes, collect the list of keys that were written or deleted and call Q.log_event.",
          "code_to_add": "saved_keys = [k for k, inp in meta_rows.items() if inp.value.strip()] + [row['key'].value for row in extra_rows if row['key'].value]\nQ.log_event('braille', job_id, 'METADATA_UPDATE', 'SUCCESS', agent='user', detail=f'Metadata updated: {len(saved_keys)} field(s)', extra_metadata={'updated_keys': saved_keys})"
        },
        {
          "file": "accessibility_mgr/ui/lp_ebraille.py",
          "function": "_metadata_dialog._save_all",
          "action": "modify",
          "description": "Same pattern with job_type='lp_ebraille'."
        },
        {
          "file": "accessibility_mgr/ui/print_jobs.py",
          "function": "_metadata_dialog._save_all",
          "action": "modify",
          "description": "Same pattern with job_type='print'."
        },
        {
          "file": "accessibility_mgr/ui/tactile_graphics.py",
          "function": "_job_detail._metadata_dialog._save_all",
          "action": "modify",
          "description": "Same pattern with job_type='tactile'."
        },
        {
          "file": "accessibility_mgr/ui/metadata_editor.py",
          "function": "_render_editor._save_all",
          "action": "modify",
          "description": "Replace the in-memory MetadataAuditService call with Q.log_event so the before/after record persists to the database. Keep the MetadataValidationService call. Remove the import of MetadataAuditService.",
          "imports_to_remove": ["from ..services.metadata_audit import MetadataAuditService"],
          "code_to_replace": "audit_events = _audit_service.bulk_record_changes(...)",
          "replacement": "Q.log_event(job_type, job_id, 'METADATA_UPDATE', 'SUCCESS', agent='operator', detail=f'Metadata updated via editor', extra_metadata={'updated_keys': list(metadata.keys()), 'previous_snapshot': existing})"
        }
      ]
    },
    {
      "id": "FIX-004",
      "priority": 4,
      "title": "Eliminate shadow database — consolidate to single SQLite file",
      "requirement": "Organization",
      "status": "open",
      "depends_on": [],
      "description": "services/sqlite_store.py creates accessibility_mgr.db alongside the main accessibility_manager.db. Services that depend on SQLiteStore write to a file that is not backed up, not queryable from the main layer, and invisible to the audit trail.",
      "files_to_delete": [
        "accessibility_mgr/services/sqlite_store.py",
        "accessibility_mgr/services/persistent_analytics.py",
        "accessibility_mgr/services/persistent_provenance.py",
        "accessibility_mgr/services/persistent_qa.py",
        "accessibility_mgr/services/distributed_queue.py",
        "accessibility_mgr/services/migrations.py"
      ],
      "files_to_modify": [
        "accessibility_mgr/api/rest_api.py",
        "accessibility_mgr/services/compliance_reporting.py"
      ],
      "changes": [
        {
          "file": "accessibility_mgr/api/rest_api.py",
          "action": "modify",
          "description": "Replace PersistentAnalyticsService and PersistentProvenanceRegistry with direct calls to db.queries functions (list_qa_runs, list_events_for_job, list_pipeline_runs). Remove imports of deleted services."
        },
        {
          "file": "accessibility_mgr/services/compliance_reporting.py",
          "action": "modify",
          "description": "Replace PersistentProvenanceRegistry with direct db.queries calls. The AuditLogService dependency can remain as it is a runtime-only in-memory log used for the compliance export signature; it does not need persistence."
        },
        {
          "note": "PersistentQAService's pipeline_run table conflicts with the main pipeline_run table in schema.py by the same name but with different columns. Once the file is deleted, the main pipeline_run table is unambiguous."
        }
      ]
    },
    {
      "id": "FIX-005",
      "priority": 5,
      "title": "Delete all dead SQLAlchemy legacy code",
      "requirement": "Organization",
      "status": "open",
      "depends_on": ["FIX-004"],
      "description": "The SQLAlchemy ORM layer (database.py, models/, and ~10 services and UI files) is legacy from a previous architecture. No active UI page uses these. They account for roughly 40% of the codebase and make the data layer ambiguous.",
      "files_to_delete": [
        "accessibility_mgr/db/database.py",
        "accessibility_mgr/models/__init__.py",
        "accessibility_mgr/models/assets.py",
        "accessibility_mgr/models/inventory.py",
        "accessibility_mgr/services/assets_service.py",
        "accessibility_mgr/services/inventory_service.py",
        "accessibility_mgr/services/file_ingestion_service.py",
        "accessibility_mgr/services/package_service.py",
        "accessibility_mgr/services/search_service.py",
        "accessibility_mgr/services/workflow_engine.py",
        "accessibility_mgr/ui/asset_detail.py",
        "accessibility_mgr/ui/assets.py",
        "accessibility_mgr/ui/categories.py",
        "accessibility_mgr/ui/inventory.py",
        "accessibility_mgr/ui/layout.py",
        "accessibility_mgr/ui/workflow_braille.py",
        "accessibility_mgr/ui/workflow_printing.py"
      ],
      "files_to_modify": [
        "accessibility_mgr/__init__.py",
        "accessibility_mgr/requirements.txt"
      ],
      "changes": [
        {
          "file": "accessibility_mgr/__init__.py",
          "action": "modify",
          "description": "Remove the 'models' entry from the aliases dict in _install_legacy_import_aliases. The db, services, and ui aliases can remain as they are still valid packages. The models alias and the SQLAlchemy fallback branch in the except clause should be removed.",
          "lines_to_remove_pattern": "alias == 'models' and exc.name == 'sqlalchemy'"
        },
        {
          "file": "accessibility_mgr/requirements.txt",
          "action": "modify",
          "description": "Remove sqlalchemy and alembic. Retain nicegui and pydantic.",
          "remove_lines": ["sqlalchemy", "alembic"]
        }
      ]
    },
    {
      "id": "FIX-006",
      "priority": 6,
      "title": "Add file attachment UI to tactile graphics jobs",
      "requirement": "Track all material types",
      "status": "open",
      "depends_on": [],
      "description": "Tactile graphics jobs have no _ingest_dialog and no file display section in the detail view. Files cannot be attached at any workflow stage despite the job_file_link table supporting it.",
      "files_to_modify": [
        "accessibility_mgr/ui/tactile_graphics.py"
      ],
      "changes": [
        {
          "action": "add_function",
          "function_name": "_ingest_dialog",
          "signature": "_ingest_dialog(job_id: int, on_done) -> None",
          "description": "Copy the _ingest_dialog implementation from braille_jobs.py verbatim. Update the job_type string passed to Q.link_file_to_job and Q.log_event from 'braille' to 'tactile'. Update step labels to use the tactile _STEP_LABELS dict.",
          "step_labels_to_use": {
            "designed": "1. Designed",
            "produced": "2. Produced",
            "qa_reviewed": "3. QA Reviewed",
            "delivered": "4. Delivered"
          },
          "source_reference": "accessibility_mgr/ui/braille_jobs.py:_ingest_dialog"
        },
        {
          "action": "modify",
          "function": "_job_detail._render",
          "description": "Add a 'Files' card to the row alongside the workflow steps card and metadata card. Copy the file display pattern from braille_jobs.py _job_detail, updating job_type to 'tactile'. Add '+ Attach File' button that calls _ingest_dialog(job_id, _refresh)."
        },
        {
          "action": "add_imports",
          "imports": ["from .components import file_use_badge"]
        }
      ]
    },
    {
      "id": "FIX-007",
      "priority": 7,
      "title": "Add workflow step tracking to 3-D print jobs",
      "requirement": "Track all material types",
      "status": "open",
      "depends_on": [],
      "description": "Print jobs are single log entries with no step-level tracking. The workflow_step table is already seeded with print stages (designed, sliced, printed, inspected, delivered) but print_job has no step columns and complete_step/revert_step do not support job_type='print'.",
      "files_to_modify": [
        "accessibility_mgr/db/schema.py",
        "accessibility_mgr/db/queries.py",
        "accessibility_mgr/ui/print_jobs.py"
      ],
      "changes": [
        {
          "file": "accessibility_mgr/db/schema.py",
          "action": "modify",
          "description": "Add five boolean step columns to the print_job CREATE TABLE statement and to the _migrate function as ALTER TABLE statements for existing databases.",
          "columns_to_add": [
            "designed   INTEGER DEFAULT 0",
            "sliced     INTEGER DEFAULT 0",
            "printed    INTEGER DEFAULT 0",
            "inspected  INTEGER DEFAULT 0",
            "delivered  INTEGER DEFAULT 0"
          ],
          "migration_sql": [
            "ALTER TABLE print_job ADD COLUMN designed   INTEGER DEFAULT 0",
            "ALTER TABLE print_job ADD COLUMN sliced     INTEGER DEFAULT 0",
            "ALTER TABLE print_job ADD COLUMN printed    INTEGER DEFAULT 0",
            "ALTER TABLE print_job ADD COLUMN inspected  INTEGER DEFAULT 0",
            "ALTER TABLE print_job ADD COLUMN delivered  INTEGER DEFAULT 0"
          ],
          "migration_location": "_migrate function — use _table_has_column guard before each ALTER"
        },
        {
          "file": "accessibility_mgr/db/queries.py",
          "action": "modify",
          "description": "Add 'print' to _STEP_TABLES and _ALLOWED_STEPS dicts so complete_step and revert_step work for print jobs.",
          "dict_additions": {
            "_STEP_TABLES": {"print": "print_job"},
            "_ALLOWED_STEPS": {"print": ["designed", "sliced", "printed", "inspected", "delivered"]}
          }
        },
        {
          "file": "accessibility_mgr/db/queries.py",
          "function": "update_print_job",
          "action": "modify",
          "description": "Add the five new step column names to the allowed set.",
          "add_to_allowed": ["designed", "sliced", "printed", "inspected", "delivered"]
        },
        {
          "file": "accessibility_mgr/ui/print_jobs.py",
          "action": "modify",
          "description": "Convert the flat table row view into a detail view pattern matching braille_jobs.py. Add a step card showing the five print stages with Mark Done / Revert buttons. Add a progress bar. The existing table can remain as the list view; clicking a row opens the detail view.",
          "constants_to_add": {
            "_PRINT_STEPS": ["designed", "sliced", "printed", "inspected", "delivered"],
            "_PRINT_STEP_LABELS": {
              "designed": "1. Designed",
              "sliced": "2. Sliced",
              "printed": "3. Printed",
              "inspected": "4. Inspected",
              "delivered": "5. Delivered"
            }
          },
          "new_functions": ["_print_job_detail(job, content_area, refresh_cb)"]
        }
      ]
    },
    {
      "id": "FIX-008",
      "priority": 8,
      "title": "Route job-detail file attachments through artifact storage",
      "requirement": "Organization / Findability",
      "status": "open",
      "depends_on": [],
      "description": "The _ingest_dialog in braille_jobs.py and lp_ebraille.py calls Q.ingest_file without project_title or student metadata, so attached files land in job_files/<uuid>.<ext> instead of artifacts/<Project Title>/. Two storage paths exist depending on which UI was used.",
      "files_to_modify": [
        "accessibility_mgr/ui/braille_jobs.py",
        "accessibility_mgr/ui/lp_ebraille.py",
        "accessibility_mgr/ui/tactile_graphics.py"
      ],
      "changes": [
        {
          "file": "accessibility_mgr/ui/braille_jobs.py",
          "function": "_ingest_dialog._save",
          "action": "modify",
          "description": "Before calling Q.ingest_file, fetch the job's existing metadata via Q.list_job_metadata('braille', job_id) and extract project context fields if present. Pass them to Q.ingest_file.",
          "metadata_keys_to_extract": {
            "project_title": "dc:title",
            "student_initials": "grade_level",
            "school_name": "dc:coverage",
            "grade_level": "grade_level",
            "subject": "dc:subject"
          },
          "note": "If the metadata keys are absent, the fields default to empty string and ingest falls back to job_files/ — acceptable fallback behavior. Alternatively, add explicit project context fields to the ingest dialog form.",
          "preferred_approach": "Add four optional text inputs to the _ingest_dialog form — Project Title, Student Initials, School, Grade/Subject — pre-populated from Q.list_job_metadata results. This makes the context explicit rather than silently derived."
        },
        {
          "file": "accessibility_mgr/ui/lp_ebraille.py",
          "function": "_ingest_dialog._save",
          "action": "modify",
          "description": "Same pattern as braille_jobs.py."
        },
        {
          "file": "accessibility_mgr/ui/tactile_graphics.py",
          "function": "_ingest_dialog._save",
          "action": "modify",
          "description": "Same pattern — applies once FIX-006 adds the ingest dialog."
        }
      ]
    },
    {
      "id": "FIX-009",
      "priority": 9,
      "title": "Replace in-memory Python search with parameterized SQL queries",
      "requirement": "Findability",
      "status": "open",
      "depends_on": [],
      "description": "search_page loads all jobs, files, and metadata into Python memory and filters with string.lower() in loops. Metadata search issues one DB round-trip per job. Needs to be replaced with SQL LIKE queries across all tables in a single or small number of parameterized calls.",
      "files_to_modify": [
        "accessibility_mgr/db/queries.py",
        "accessibility_mgr/ui/search.py"
      ],
      "changes": [
        {
          "file": "accessibility_mgr/db/queries.py",
          "action": "add_function",
          "function_name": "search_all",
          "signature": "search_all(query: str, limit: int = 200) -> dict[str, list[dict]]",
          "description": "Execute a single SQL query per category using LIKE with the search term. Return a dict keyed by result type.",
          "sql_queries": {
            "braille_jobs": "SELECT id, title, braille_type, requester, priority, created_at FROM braille_job WHERE title LIKE ? OR requester LIKE ? OR notes LIKE ? ORDER BY created_at DESC LIMIT ?",
            "lp_jobs": "SELECT id, title, job_type, requester, priority, created_at FROM lp_ebraille_job WHERE title LIKE ? OR requester LIKE ? OR notes LIKE ? ORDER BY created_at DESC LIMIT ?",
            "tactile_jobs": "SELECT id, title, tactile_type, requester, priority, created_at FROM tactile_graphics_job WHERE title LIKE ? OR requester LIKE ? OR notes LIKE ? ORDER BY created_at DESC LIMIT ?",
            "print_jobs": "SELECT id, object_name, file_name, requester, successful, printed_at FROM print_job WHERE object_name LIKE ? OR requester LIKE ? OR file_name LIKE ? OR notes LIKE ? ORDER BY printed_at DESC LIMIT ?",
            "files": "SELECT id, original_name, stored_path, file_use, format_name, checksum_sha256, created_at FROM file_object WHERE original_name LIKE ? OR stored_path LIKE ? OR format_name LIKE ? OR encoding LIKE ? OR checksum_sha256 = ? ORDER BY created_at DESC LIMIT ?",
            "metadata": "SELECT jm.job_type, jm.job_id, jm.meta_key, jm.meta_value FROM job_metadata jm WHERE jm.meta_key LIKE ? OR jm.meta_value LIKE ? ORDER BY jm.job_type, jm.job_id LIMIT ?",
            "events": "SELECT me.job_type, me.job_id, me.event_type, me.agent, me.detail, me.event_datetime FROM metadata_event me WHERE me.detail LIKE ? OR me.agent LIKE ? OR me.event_type LIKE ? ORDER BY me.event_datetime DESC LIMIT ?"
          },
          "parameter_pattern": "term = f'%{query}%' — used for all LIKE params; raw query used for checksum exact-match",
          "return_keys": ["braille_jobs", "lp_jobs", "tactile_jobs", "print_jobs", "files", "metadata", "events"],
          "add_to___all__": true
        },
        {
          "file": "accessibility_mgr/ui/search.py",
          "function": "_execute",
          "action": "rewrite",
          "description": "Replace all Q.list_*() calls and Python filtering loops with a single call to Q.search_all(q). Unpack the returned dict into the existing section renderer. Add an 'Events' result section to display matching event log entries.",
          "new_section": {
            "name": "Event Log",
            "render_fields": ["event_datetime", "job_type", "job_id", "event_type", "agent", "detail"]
          }
        }
      ]
    },
    {
      "id": "FIX-010",
      "priority": 10,
      "title": "Add student entity table and link jobs to students",
      "requirement": "Findability",
      "status": "open",
      "depends_on": ["FIX-007"],
      "description": "requester is a free-text string on every job table. Spelling variations mean the same student cannot be reliably found across jobs. A student table with a primary key allows all jobs for a student to be retrieved in one query.",
      "files_to_modify": [
        "accessibility_mgr/db/schema.py",
        "accessibility_mgr/db/queries.py",
        "accessibility_mgr/ui/braille_jobs.py",
        "accessibility_mgr/ui/lp_ebraille.py",
        "accessibility_mgr/ui/tactile_graphics.py",
        "accessibility_mgr/ui/print_jobs.py",
        "accessibility_mgr/app.py"
      ],
      "files_to_create": [
        "accessibility_mgr/ui/students.py"
      ],
      "changes": [
        {
          "file": "accessibility_mgr/db/schema.py",
          "action": "modify",
          "description": "Add student table to _SCHEMA_SQL before the jobs section. Add student_id nullable foreign key column to all four job tables. Add migration ALTER TABLE statements to _migrate for existing databases.",
          "table_definition": "CREATE TABLE IF NOT EXISTS student (\n    id           INTEGER PRIMARY KEY AUTOINCREMENT,\n    last_name    TEXT NOT NULL,\n    first_name   TEXT NOT NULL,\n    school       TEXT,\n    grade        TEXT,\n    preferred_formats TEXT,\n    notes        TEXT,\n    active       INTEGER DEFAULT 1,\n    created_at   TEXT DEFAULT (datetime('now')),\n    updated_at   TEXT DEFAULT (datetime('now'))\n);",
          "migration_sql": [
            "ALTER TABLE braille_job ADD COLUMN student_id INTEGER REFERENCES student(id)",
            "ALTER TABLE lp_ebraille_job ADD COLUMN student_id INTEGER REFERENCES student(id)",
            "ALTER TABLE tactile_graphics_job ADD COLUMN student_id INTEGER REFERENCES student(id)",
            "ALTER TABLE print_job ADD COLUMN student_id INTEGER REFERENCES student(id)"
          ]
        },
        {
          "file": "accessibility_mgr/db/queries.py",
          "action": "add_functions",
          "functions": [
            "list_students(active_only: bool = True) -> list[dict]",
            "get_student(student_id: int) -> Optional[dict]",
            "add_student(last_name, first_name, school, grade, preferred_formats, notes) -> int",
            "update_student(student_id, **fields) -> None",
            "delete_student(student_id) -> None",
            "list_jobs_for_student(student_id: int) -> dict[str, list[dict]] — returns {'braille': [...], 'lp_ebraille': [...], 'tactile': [...], 'print': [...]}"
          ],
          "add_to___all__": true
        },
        {
          "file": "accessibility_mgr/ui/students.py",
          "action": "create",
          "description": "New page. List all students with school, grade, active status. Clicking a student shows a detail view with all their jobs across all types grouped by job type, with status indicators. Include add/edit/deactivate dialogs. The student detail view is the primary cross-material-type view for a single person.",
          "page_function": "students_page(content_area: ui.element) -> None"
        },
        {
          "file": "accessibility_mgr/ui/braille_jobs.py",
          "function": "_job_dialog",
          "action": "modify",
          "description": "Replace the free-text Requester input with a student selector dropdown (populated from Q.list_students()) plus a '+ New Student' quick-add button. Keep the requester text field as a fallback for non-student requesters (e.g., teachers, libraries). Add student_id to the data dict returned by on_save."
        },
        {
          "file": "accessibility_mgr/app.py",
          "action": "modify",
          "description": "Add students_page to PAGE_DEFINITIONS under the Production group.",
          "new_entry": {
            "name": "Students",
            "icon": "person",
            "module": "accessibility_mgr.ui.students",
            "function": "students_page",
            "description": "Student records and cross-job history",
            "group": "Production"
          }
        }
      ]
    },
    {
      "id": "FIX-011",
      "priority": 11,
      "title": "Standardize file_use vocabulary across schema and UI",
      "requirement": "Organization",
      "status": "open",
      "depends_on": [],
      "description": "The material_category seed data uses MASTER but the UI _FILE_USES lists use ORIGINAL. Records written through the ingestion page may have ORIGINAL or MASTER as file_use depending on path. Standardize on ORIGINAL throughout (METS uses MASTER but ORIGINAL is more intuitive for this team's workflow).",
      "decision": "Standardize on: ORIGINAL, DERIVATIVE, INTERMEDIATE, SOURCE, REFERENCE",
      "files_to_modify": [
        "accessibility_mgr/db/schema.py",
        "accessibility_mgr/ui/braille_jobs.py",
        "accessibility_mgr/ui/lp_ebraille.py",
        "accessibility_mgr/ui/ingestion.py"
      ],
      "changes": [
        {
          "file": "accessibility_mgr/db/schema.py",
          "action": "modify",
          "description": "In the INSERT OR IGNORE INTO material_category seed block, change the file_use section value 'MASTER' to 'ORIGINAL' and label 'Master' to 'Original'.",
          "find": "('file_use','MASTER',       'Master',       1)",
          "replace": "('file_use','ORIGINAL',     'Original',     1)"
        },
        {
          "file": "accessibility_mgr/ui/braille_jobs.py",
          "action": "modify",
          "description": "Verify _FILE_USES already contains 'ORIGINAL' — no change needed if so.",
          "current_value": ["ORIGINAL", "DERIVATIVE", "INTERMEDIATE", "SOURCE", "REFERENCE"],
          "status": "already_correct"
        },
        {
          "file": "accessibility_mgr/ui/lp_ebraille.py",
          "action": "modify",
          "description": "Verify _FILE_USES already contains 'ORIGINAL' — no change needed if so.",
          "status": "already_correct"
        },
        {
          "file": "accessibility_mgr/ui/ingestion.py",
          "action": "modify",
          "description": "Verify FILE_USES list defaults to 'ORIGINAL' — no change needed if so.",
          "status": "already_correct"
        },
        {
          "note": "If the database already contains records with file_use='MASTER', run a one-time migration: UPDATE file_object SET file_use = 'ORIGINAL' WHERE file_use = 'MASTER'"
        }
      ]
    },
    {
      "id": "FIX-012",
      "priority": 12,
      "title": "Link QA runs to specific jobs and write to job event log",
      "requirement": "Auditability",
      "status": "open",
      "depends_on": [],
      "description": "QA tool runs from the QA Tooling page pass job_type=None and job_id=None to Q.log_qa_run, so no QA result appears in any job's event log. There is no way to know which EPUB file a specific EPUBCheck run was validating in relation to a production job.",
      "files_to_modify": [
        "accessibility_mgr/ui/qa.py",
        "accessibility_mgr/services/qa_service.py"
      ],
      "changes": [
        {
          "file": "accessibility_mgr/ui/qa.py",
          "function": "_run_tool_dialog",
          "action": "modify",
          "description": "Add two optional fields to the run dialog: a job type selector and a job ID input. Populate job type options from the list of active job types. Pass the selected job_type and job_id to QAService.run_tool.",
          "new_inputs": [
            "job_type_sel: ui.select(['(none)', 'braille', 'lp_ebraille', 'tactile', 'print'], value='(none)', label='Link to Job Type')",
            "job_id_inp: ui.input('Job ID (optional)', placeholder='numeric ID')"
          ]
        },
        {
          "file": "accessibility_mgr/services/qa_service.py",
          "function": "QAService.run_tool",
          "action": "modify",
          "description": "After Q.log_qa_run, if job_type and job_id are provided, also call Q.log_event to write a QA_RUN event to the job's metadata_event record.",
          "code_to_add": "if job_type and job_id:\n    Q.log_event(job_type, job_id, 'QA_RUN', 'SUCCESS' if result.success else 'FAILURE', agent='system', detail=f'{name}: {\"PASS\" if result.success else \"FAIL\"}', extra_metadata={'tool': name, 'command': result.command})"
        }
      ]
    },
    {
      "id": "FIX-013",
      "priority": 13,
      "title": "Surface backup status and manual trigger in Admin UI",
      "requirement": "Operations",
      "status": "open",
      "depends_on": [],
      "description": "BackupService.status() and list_backup_log() are never called from any UI page. There is no way for an operator to know when the last backup ran, whether it succeeded, or to trigger a manual backup.",
      "files_to_modify": [
        "accessibility_mgr/ui/admin.py"
      ],
      "changes": [
        {
          "file": "accessibility_mgr/ui/admin.py",
          "action": "modify",
          "description": "Add a 'Backups' tab to the admin page tab set alongside the existing tabs.",
          "new_tab_name": "Backups",
          "tab_content_function": "_backup_section(container: ui.element) -> None",
          "ui_elements": [
            "Status card: scheduler active/inactive, backup count, last backup path and size (from BackupService.status())",
            "'Run Backup Now' button: calls BackupService.run_backup(trigger='manual') in a background thread, shows spinner, refreshes on completion",
            "Recent backups table: last 20 entries from Q.list_backup_log() showing path, size_bytes, trigger, status, created_at"
          ],
          "imports_to_add": [
            "from ..services.backup_service import BackupService",
            "import threading"
          ]
        }
      ]
    },
    {
      "id": "FIX-014",
      "priority": 14,
      "title": "Include event log content and file checksums in search",
      "requirement": "Findability",
      "status": "open",
      "depends_on": ["FIX-009"],
      "description": "The search page cannot find operator notes, event detail text, agent names, or file SHA-256 checksums. If FIX-009 is implemented first, this becomes a matter of adding the events and checksum queries to search_all and rendering the results.",
      "files_to_modify": [
        "accessibility_mgr/db/queries.py",
        "accessibility_mgr/ui/search.py"
      ],
      "changes": [
        {
          "file": "accessibility_mgr/db/queries.py",
          "function": "search_all",
          "action": "modify",
          "description": "The events SQL query is already specified in FIX-009. Ensure the files query includes checksum_sha256 = ? (exact match) in addition to the LIKE clauses on name, path, format.",
          "note": "SHA-256 hashes are 64-char hex strings; an exact match clause is more useful than LIKE for checksums."
        },
        {
          "file": "accessibility_mgr/ui/search.py",
          "action": "modify",
          "description": "Add an 'Event Log' section to the search results display. Render each matching event with: datetime, job_type + job_id as a clickable link, event_type badge, agent, and detail text.",
          "event_row_fields": ["event_datetime", "job_type", "job_id", "event_type", "agent", "detail"]
        }
      ]
    },
    {
      "id": "FIX-015",
      "priority": 15,
      "title": "Add faceted reporting page by student, school, grade, and material type",
      "requirement": "Findability",
      "status": "open",
      "depends_on": ["FIX-009", "FIX-010"],
      "description": "There is no aggregate view answering 'show me everything produced for Legacy Jr. High this year' or 'all active Grade 7 jobs'. The search page finds individual records; a reports page provides structured multi-field filtering with summary counts.",
      "files_to_create": [
        "accessibility_mgr/ui/reports.py"
      ],
      "files_to_modify": [
        "accessibility_mgr/db/queries.py",
        "accessibility_mgr/app.py"
      ],
      "changes": [
        {
          "file": "accessibility_mgr/db/queries.py",
          "action": "add_function",
          "function_name": "report_jobs",
          "signature": "report_jobs(school: Optional[str] = None, grade: Optional[str] = None, job_type: Optional[str] = None, status: Optional[str] = None, date_from: Optional[str] = None, date_to: Optional[str] = None, student_id: Optional[int] = None) -> dict",
          "description": "Query all job tables with optional filter parameters applied as SQL WHERE conditions. Join to student table when student_id is provided. Join to job_metadata to filter by school/grade when those fields are stored as metadata rather than on the job record directly. Return counts and job lists grouped by type.",
          "return_shape": {
            "total_jobs": "int",
            "by_type": {"braille": "int", "lp_ebraille": "int", "tactile": "int", "print": "int"},
            "jobs": [{"id": "int", "title": "str", "job_type": "str", "requester": "str", "priority": "str", "status": "str — derived from step completion", "created_at": "str"}]
          }
        },
        {
          "file": "accessibility_mgr/ui/reports.py",
          "action": "create",
          "description": "Reports page with filter controls and results table.",
          "filter_controls": [
            "School name text input (or select from distinct values in job_metadata where meta_key='dc:coverage' or student.school)",
            "Grade level text input",
            "Material type multi-select: Braille, Large Print, eBraille, EPUB3/DAISY, Tactile, 3-D Print",
            "Status select: All, In Progress (any step done, not all done), Delivered (all steps done), Not Started",
            "Date range: from/to date inputs against created_at",
            "Student select (from Q.list_students() — available after FIX-010)"
          ],
          "results_display": [
            "Summary row: N total jobs, breakdown by type",
            "Sortable table: Job Title, Type, Requester/Student, School, Grade, Priority, Progress bar, Created date",
            "Export to CSV button: writes results to a downloadable CSV"
          ],
          "page_function": "reports_page(content_area: ui.element) -> None"
        },
        {
          "file": "accessibility_mgr/app.py",
          "action": "modify",
          "description": "Add reports_page to PAGE_DEFINITIONS under the Overview group.",
          "new_entry": {
            "name": "Reports",
            "icon": "summarize",
            "module": "accessibility_mgr.ui.reports",
            "function": "reports_page",
            "description": "Filter and export jobs by school, grade, type, and status",
            "group": "Overview"
          }
        }
      ]
    },
    {
      "id": "FIX-016",
      "priority": 16,
      "title": "Add delivery tracking fields to all job tables",
      "requirement": "Track all material types",
      "status": "open",
      "depends_on": ["FIX-007"],
      "description": "The 'Delivered' step is a boolean checkbox with no record of how, to whom, or when the materials were physically or digitally delivered. Delivery confirmation is important for compliance and IEP documentation.",
      "files_to_modify": [
        "accessibility_mgr/db/schema.py",
        "accessibility_mgr/db/queries.py",
        "accessibility_mgr/ui/braille_jobs.py",
        "accessibility_mgr/ui/lp_ebraille.py",
        "accessibility_mgr/ui/tactile_graphics.py",
        "accessibility_mgr/ui/print_jobs.py"
      ],
      "changes": [
        {
          "file": "accessibility_mgr/db/schema.py",
          "action": "modify",
          "description": "Add delivery columns to braille_job, lp_ebraille_job, tactile_graphics_job, and print_job tables. Add corresponding ALTER TABLE migrations.",
          "columns_to_add": [
            "delivery_date       TEXT",
            "delivery_method     TEXT",
            "delivery_recipient  TEXT",
            "delivery_notes      TEXT"
          ],
          "delivery_method_options": ["Physical copy", "Email", "Learning Management System", "USB/media", "Pickup", "Other"]
        },
        {
          "file": "accessibility_mgr/db/queries.py",
          "action": "modify",
          "description": "Add delivery columns to the allowed set in update_braille_job, update_lp_job, update_tactile_job, and update_print_job.",
          "add_to_allowed": ["delivery_date", "delivery_method", "delivery_recipient", "delivery_notes"]
        },
        {
          "note": "The delivery fields should be surfaced in the job detail UI when the 'Mark Done' button is clicked for the Delivered step. Rather than immediately completing the step, show a small inline form capturing delivery_method, delivery_date (defaulting to today), and delivery_recipient before writing the step completion and delivery fields."
        }
      ]
    },
    {
      "id": "FIX-017",
      "priority": 17,
      "title": "Add dry-run preview to metadata key backfill tool",
      "requirement": "Organization",
      "status": "open",
      "depends_on": [],
      "description": "The backfill tool in Admin > Metadata Options has no preview step. A misconfigured run could silently merge keys. The Q.backfill_metadata_keys function already returns a mappings dict that can be shown before confirmation.",
      "files_to_modify": [
        "accessibility_mgr/ui/admin.py"
      ],
      "changes": [
        {
          "file": "accessibility_mgr/ui/admin.py",
          "function": "_metadata_options_section._run_backfill",
          "action": "modify",
          "description": "Replace the single confirm_dialog with a two-step flow: (1) call a new dry-run function that returns proposed mappings without writing, display the mappings in a preview dialog; (2) only after the user confirms the preview does the actual backfill execute.",
          "new_helper_function": "preview_backfill_metadata_keys(approved_keys: list[str]) -> dict — same logic as backfill_metadata_keys but skips the UPDATE/DELETE statements, returning only the mappings and skipped_keys",
          "preview_dialog_content": "Table showing: Non-approved key | Proposed canonical key | Usage count | Action (Rename / Skip). Skipped keys listed separately with explanation that no close match was found.",
          "add_to_queries___all__": "preview_backfill_metadata_keys"
        }
      ]
    }
  ]
}