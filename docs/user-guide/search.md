# Search

Navigate to **Overview → Search** for global full-text search across all jobs,
files, metadata, students, and the event log.

---

## 🔍 How It Works

APM uses **SQLite FTS5** (Full-Text Search) when available.  It falls back to
`LIKE '%term%'` queries on databases that pre-date migration `m009`.

### What is searched

| Category | Fields |
|----------|--------|
| Braille Jobs | title, requester, notes |
| LP / eBraille / EPUB3 Jobs | title, requester, notes |
| Tactile Graphics Jobs | title, requester, notes |
| 3-D Print Jobs | object_name, file_name, requester, notes |
| Students | last_name, first_name, school, notes |
| Files | original_name, stored_path, format_name, encoding |
| Metadata | meta_key, meta_value |
| Event Log | event_type, agent, detail |

---

## 🔑 SHA-256 Checksum Search

If you paste a full **64-character hex** SHA-256 string, APM performs an
**exact match** against `file_object.checksum_sha256` in addition to the
normal LIKE search.  This is useful for verifying file integrity or locating
a specific ingested file by its fingerprint.

---

## 📤 Using Search Results

Search results are grouped by category.  Each result shows the most relevant
fields for quick identification.  Click the job title or file name (where
applicable) to navigate directly to that record.

---

## ⚡ Performance

- FTS5 searches are typically under 50 ms for databases with thousands of rows.
- LIKE fallback is slower on very large databases.  See
  [Performance](../administration/performance.md) for FTS rebuild instructions.

---

## 💡 Tips

- Search is case-insensitive.
- Partial words match (e.g. `math` matches `mathematics`).
- Press `Enter` in the search box to submit without clicking the button.
- To find all jobs for a student, use the **Students** page → **View** →
  job history, rather than searching by name.
