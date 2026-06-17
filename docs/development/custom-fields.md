# Custom Metadata Fields

APM supports extending job metadata through two mechanisms: the **Admin UI**
(no code required) and direct database manipulation.

---

## 🖱️ Via Admin UI (recommended)

1. Go to **Admin → Metadata Options**.
2. Select the group where the new key belongs:
   - **Dublin Core** — `dc:*` namespace fields
   - **eBraille Profile** — production-specific fields
   - **METS / PREMIS** — archival metadata fields
3. Click **+ Add Key**.
4. Enter the metadata key (e.g. `dc:audience`) and display label.
5. Click **Save**.

The key appears immediately in all metadata editor dropdowns and the
**Additional Allowed Fields** section of job detail views.

---

## 🗄️ Via Database

Insert directly into `material_category`:

```sql
INSERT INTO material_category (section, value, label, sort_order)
VALUES ('metadata_dublin_core', 'dc:audience', 'Audience', 16);
```

Valid sections: `metadata_dublin_core`, `metadata_ebraille_profile`,
`metadata_mets_premis`.

---

## 💾 Storing Values

Metadata is stored in the `job_metadata` table as key-value pairs:

```sql
INSERT INTO job_metadata (job_type, job_id, meta_key, meta_value)
VALUES ('braille', 42, 'dc:audience', 'Students Grade 7-9');
```

The Python helper:

```python
from accessibility_mgr.db import queries as Q
Q.set_job_metadata("braille", 42, "dc:audience", "Students Grade 7-9")
```

---

## 🔍 Querying Custom Metadata

```python
# Get all metadata for a job
meta = Q.list_job_metadata("braille", 42)
# {'dc:title': '...', 'dc:audience': 'Students Grade 7-9', ...}

# Get a single field
val = Q.get_job_metadata("braille", 42, "dc:audience")

# Search across all jobs
results = Q.search_all("Students Grade 7")
# results["metadata"] contains matching key-value pairs
```

---

## 🔑 Backfilling Typo Keys

If historical data has inconsistent key names, use the backfill tool
(Admin → Metadata Options → **Backfill Typo Keys**) to preview and apply
fuzzy-matched normalisation.

See [Categories](../administration/categories.md#metadata-key-backfill) for
the full workflow.
