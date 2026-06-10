# Implementation Plan

This document targets the six major remediation areas identified during the
architecture audit.

## Completed updates since initial plan

- Added artifact-based ingestion and structured artifact naming conventions.
- Added metadata governance controls, option catalogs, and admin backfill
  actions for key normalization.
- Added EPUB3/DAISY production workflow visibility and dashboard surfacing.
- Reclassified DAISY Pipeline under Pipelines instead of QA Tooling.
- Improved electronics inventory category UX to display empty categories and
  support required inline category creation.
- Mounted the REST API under `/api` with optional API-key authentication.
- Added export summaries, bulk actions, quick-create shortcuts, and upcoming-deadline widgets.
- Added FTS5-backed search indexes with a SQLite fallback path.
- Added workflow step completion timestamps and serialized backup execution.

---

## 1. UI Exposure

### UI Exposure Goal

Expose all metadata, workflow, and asset-management capabilities through the
NiceGUI interface.

### Remaining Work

- Expose the Asset Registry as a first-class page in the main app sidebar.
- Add workflow timeline visualization in dashboard and job-level views.
- Expand fabrication dashboards with trend/throughput views beyond current job lists.

### Incomplete Deliverables

- Add direct sidebar entry for Asset Registry.
- Add timeline widgets to production pages.

---

## 2. CRUD Tooling

### CRUD Tooling Goal

Provide complete create/read/update/delete support for all workflow entities.

### Remaining CRUD Domains

| Domain          | Priority |
| --------------- | -------- |
| Projects        | High     |
| Assets          | High     |
| Workflow events | Medium   |
| Devices         | Medium   |
| Deliveries      | Medium   |

### Remaining Technical Work

- Complete project CRUD in primary UI flows.
- Complete asset CRUD integration from navigation and detail pages.
- Add workflow event, device, and delivery CRUD UIs.
- Add validation coverage for remaining CRUD domains.

---

## 3. Workflow Orchestration

### Workflow Orchestration Goal

Track all accessibility production steps from ingestion through delivery.

### Workflow Domains

### Braille

- OCR
- Cleanup
- Formatting
- Translation
- Proofreading
- Embossing
- Packaging
- Delivery

### Accessible Documents

- Semantic cleanup
- Accessibility validation
- EPUB generation
- DAISY generation
- PDF remediation

### 3-D Printing

- CAD ingestion
- Slicer configuration
- G-code generation
- Print execution
- QA validation
- Assembly tracking

### Planned Features (Workflow)

- Workflow timelines
- Status transitions
- Assignment tracking
- Approval checkpoints
- Automated notifications

---

## 4. Metadata Editing Interfaces

### Metadata Editing Goal

Support flexible metadata editing inspired by METS/PREMIS workflows.

### Required Metadata Categories

### Descriptive

- Title
- Subject
- Keywords
- Language
- Accessibility need

### Technical

- OCR engine
- Translation engine
- Printer profile
- Embosser settings

### Workflow

- Revision notes
- QA status
- Operator assignments

### Preservation

- Checksums
- Provenance
- Derivative chains

### Remaining Features (Metadata)

- Dynamic metadata templates
- Metadata inheritance
- Batch metadata editing

---

## 5. File Ingestion Pipelines

### File Ingestion Goal

Track all incoming and generated assets.

### Supported Asset Types

- DOCX
- PDF
- EPUB
- BRF
- PEF
- TXT
- HTML
- STL
- 3MF
- G-code
- Images

### Remaining Features (Ingestion)

- Automatic metadata extraction
- Derivative generation tracking
- OCR pipeline integration

---

## 6. Lineage and Provenance Visualization

### Lineage and Provenance Goal

Visualize relationships between source files, derivatives, workflow events,
and physical outputs.

### Planned Features (Lineage)

- Asset graph visualization
- Parent/child lineage trees
- Workflow replay views
- Revision comparison
- Provenance timelines
- Delivery history

## Long-Term Goal

Create a preservation-aware accessibility production graph system similar to:

- OCR-D workspaces
- METS structural maps
- Digital preservation lineage systems
