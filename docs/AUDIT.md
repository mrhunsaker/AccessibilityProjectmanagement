# Accessibility Project Manager Audit

Date: 2026-05-09

---

# Executive Summary

The project has successfully transitioned away from a placeholder NiceGUI
bootstrap and now contains the foundation of a modular web-based accessibility
production management system.

The repository currently demonstrates:

- A functioning NiceGUI application shell
- SQLite-backed persistence
- Modular UI architecture
- Production workflow concepts
- Inventory tracking concepts
- Print production tracking
- Accessibility-oriented operational goals

However, the repository is still in a transitional state between:

1. The original Textual/TUI implementation
2. The NiceGUI migration target

Several architectural areas require expansion before the system fully supports
enterprise-grade accessibility production management.

---

# Current Functional Areas

## Operational Dashboard

Status: PARTIALLY IMPLEMENTED

Existing functionality:

- Inventory alerts
- Workflow statistics
- Job summaries
- Print job summaries
- Priority indicators
- Low-stock monitoring

Recommendations:

- Add configurable dashboard widgets
- Add saved views
- Add queue prioritization
- Add due dates and SLA tracking
- Add operator workload visibility

---

## Inventory System

Status: FOUNDATIONAL

Existing tracked domains:

- Filament
- Braille paper
- Electronics
- Print supplies

Recommendations:

- Add barcode/QR support
- Add vendor metadata
- Add procurement workflows
- Add minimum inventory thresholds
- Add batch/lot tracking
- Add consumable history
- Add inventory transaction logs

---

## Braille Production Workflow

Status: CONCEPTUALLY STRONG / IMPLEMENTATION PARTIAL

Current workflow model:

1. Digitized
2. Formatted
3. Brailled
4. Proofread
5. Delivered

Required improvements:

- Multiple braille file revisions
- BRF metadata tracking
- Embosser metadata
- Translation engine metadata
- Validation tracking
- Proofreading annotations
- Version graph/history
- Digital preservation metadata

Recommended stored assets:

- Source documents
- OCR text
- Cleaned text
- Translation configs
- BRF files
- PEF files
- Embosser-ready files
- QA reports
- Delivery packages

---

## Large Print / eBraille Workflow

Status: PARTIAL

Required additions:

- DAISY metadata
- EPUB metadata
- Accessibility validation reports
- Font/layout presets
- Export history
- Packaging metadata

---

## 3-D Printing Workflow

Status: STRONG FOUNDATION

Existing concepts:

- Printer tracking
- Filament usage
- Success/failure logging
- File indexing

Required additions:

- STL metadata
- Slicer profile metadata
- G-code generation history
- Print parameter snapshots
- Accessibility object categorization
- Tactile graphics metadata
- Assistive device metadata
- Maintenance logs
- Multi-part assembly relationships

Recommended file tracking:

- CAD source
- Mesh revisions
- Slicer project files
- Generated G-code
- Printer logs
- QA photographs
- Calibration profiles

---

# Metadata Architecture Requirements

The current repository does not yet fully implement lifecycle metadata
management.

The system should evolve toward a flexible metadata architecture inspired by:

- METS
- PREMIS
- OCR-D workspace models
- Digital preservation workflows

But adapted for operational accessibility production.

---

# Recommended Metadata Model

Each project/job should support:

## Core Descriptive Metadata

- Title
- Description
- Requestor
- Organization
- Accessibility need
- Language
- Subject
- Tags
- Priority
- Due date

## Technical Metadata

- File formats
- Processing tools
- Translation engines
- OCR engines
- Slicer software
- Printer profiles
- Embosser settings
- Validation status

## Workflow Metadata

- Current stage
- Operator history
- Revision history
- Approval checkpoints
- QA outcomes
- Delivery tracking

## Preservation Metadata

- File hashes
- Generation timestamps
- Parent/child relationships
- Derivative chains
- Provenance records

---

# Database Recommendations

The current schema should evolve toward:

## Core Entities

- projects
- jobs
- assets
- asset_versions
- metadata_records
- workflow_events
- operators
- devices
- processing_steps
- deliveries

## Asset-Centric Architecture

Every generated file or physical object should become a tracked asset.

Examples:

- BRF file
- PEF file
- EPUB file
- STL file
- G-code file
- Printed tactile object
- Embossed braille copy

Each asset should support:

- Metadata
- Revision history
- Parent relationships
- Processing lineage
- QA records
- Notes
- Tags

---

# Accessibility Review

The project direction aligns well with accessibility-focused production.

Additional recommendations:

- Full keyboard navigation
- WCAG AA/AAA contrast validation
- Screen-reader testing
- Semantic HTML auditing
- Reduced-motion support
- Dyslexia-friendly typography options
- Large-text mode
- ARIA landmark coverage

---

# Immediate Development Priorities

## High Priority

1. Stabilize NiceGUI architecture
2. Implement unified project/job model
3. Add asset metadata system
4. Add file lineage tracking
5. Add revision/version support
6. Add database migrations
7. Replace remaining placeholder UI modules

## Medium Priority

1. Add authentication
2. Add role-based access
3. Add reporting/exporting
4. Add OCR workflow integration
5. Add tactile graphics workflow support

## Long-Term

1. Distributed processing
2. Multi-user collaboration
3. API integrations
4. Preservation exports
5. Workflow automation
6. Accessibility validation pipelines
