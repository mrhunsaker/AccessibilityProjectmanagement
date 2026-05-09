# Implementation Plan

This document targets the six major remediation areas identified during the
architecture audit.

---

# 1. UI Exposure

## Goal

Expose all metadata, workflow, and asset-management capabilities through the
NiceGUI interface.

## Required Work

- Add project management UI
- Add asset browser
- Add metadata editor
- Add lineage explorer
- Add workflow timeline visualization
- Add inventory dashboards
- Add fabrication dashboards

## Immediate Deliverables

- Asset Registry page
- Workflow dashboard integration
- Accessible sidebar navigation

---

# 2. CRUD Tooling

## Goal

Provide complete create/read/update/delete support for all workflow entities.

## Required CRUD Domains

| Domain | Priority |
|---|---|
| Projects | High |
| Jobs | High |
| Assets | High |
| Metadata | High |
| Inventory | High |
| Workflow events | Medium |
| Devices | Medium |
| Deliveries | Medium |

## Technical Direction

- Centralized database service layer
- Typed data access methods
- Reusable NiceGUI forms
- Validation logic
- Accessible form labeling

---

# 3. Workflow Orchestration

## Goal

Track all accessibility production steps from ingestion through delivery.

## Workflow Domains

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

## Planned Features

- Workflow timelines
- Status transitions
- Assignment tracking
- Approval checkpoints
- Automated notifications

---

# 4. Metadata Editing Interfaces

## Goal

Support flexible metadata editing inspired by METS/PREMIS workflows.

## Required Metadata Categories

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

## Planned Features

- Dynamic metadata templates
- JSON metadata editor
- Structured validation
- Metadata inheritance
- Batch metadata editing

---

# 5. File Ingestion Pipelines

## Goal

Track all incoming and generated assets.

## Supported Asset Types

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

## Planned Features

- File upload UI
- Automatic metadata extraction
- Checksum generation
- MIME identification
- Derivative generation tracking
- OCR pipeline integration

---

# 6. Lineage and Provenance Visualization

## Goal

Visualize relationships between source files, derivatives, workflow events,
and physical outputs.

## Planned Features

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
