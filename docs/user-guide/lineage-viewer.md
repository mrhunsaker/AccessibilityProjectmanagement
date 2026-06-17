# Lineage Viewer

The **Lineage Viewer** shows the relationships between files and the jobs they
are attached to, visualised as a Mermaid graph.

Navigate to **Metadata & Files → Lineage Viewer**.

---

## 📊 Lineage Graph

The graph renders automatically from `file_object`, `job_file_link`, and all
job tables.  Each file is a rectangular node; jobs are shown as parallelogram
nodes labelled by type.

Edges run from **job → file**, indicating that the job produced or uses the file.

### Graph Limits

To keep the graph renderable, it is capped at **50 nodes**.  If your registry
is larger, a warning banner appears.  Use the filter/search on the job pages
to narrow down to specific jobs and their files.

---

## 📋 File Registry Table

Below the graph is a paginated table of all ingested files (50 per page):

| Column | Description |
|--------|-------------|
| File Name | Original filename at time of ingestion |
| Use | File use classification (ORIGINAL, DERIVATIVE, etc.) |
| Format | Format name (BRF, PDF, STL …) |
| Size | Human-readable file size |
| SHA-256 | First 12 characters of the checksum (hover for full hash) |
| Ingested | Date of ingestion |

---

## 🔍 Finding a File by Checksum

Copy the full SHA-256 hex string and paste it into the **Search** page.
An exact match is performed against `file_object.checksum_sha256`.

---

## 🔗 Provenance Events

The lineage viewer also loads provenance events from the in-memory
`ProvenanceRegistry`.  In development mode (`ACCESSMAN_DEV=1`), three seed
events are added automatically so the registry is not empty on first load.

Provenance events are separate from the per-job `metadata_event` table.
They are registered by API-layer operations (workflow enqueue, etc.) and by
direct calls to `ProvenanceRegistry.register_event()`.
