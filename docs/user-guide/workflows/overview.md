# Production Workflows Overview

**Understand the common patterns across all accessibility production workflows.**

---

## 🔄 Workflow Lifecycle

All jobs follow a similar lifecycle with these stages:

```mermaid
graph LR
    A[Created] --> B[Pending]
    B --> C[In Progress]
    C --> D[QA Review]
    D --> E[Completed]
    D --> F[Needs Revision]
    F --> C
    E --> G[Delivered]
    C --> H[On Hold]
    H --> C

## 📋 Common Workflow Features
### Status Tracking

| Status | Description | Color | Actions Available |
| --- | --- | --- | --- |
| Created | Job record created, not yet started | Gray | Start, Edit, Delete |
| Pending | Awaiting assignment or resources | Blue | Assign, Start, Cancel |
| In Progress | Actively being worked on | Yellow | Update, Pause, Complete |
| QA Review | Awaiting quality assurance | Purple | Approve, Reject |
| Needs Revision | Failed QA, requires fixes | Orange | Revise, Cancel |
| Completed | All steps finished | Green | Deliver, Archive |
| Delivered | Sent to recipient | Dark Green | Archive |
| On Hold | Temporarily paused | Red | Resume, Cancel |
| Cancelled | Job abandoned | Black | Delete, Restore |

### Step Management

Each workflow consists of configurable steps:

1. Step Completion: Mark steps as complete 
2. Reversion: Roll back to previous steps
3. Skipping: Optional steps can be skipped
4. Notes: Add comments at each step
5. Attachments: Upload files for each step

### Event Logging

Every action generates an audit event:

- Who performed the action
- When it occurred
- What changed
- Previous/next states

## 🔗 Cross-Workflow Features

Student Linking

- Single student: Track all jobs for one student
- Group jobs: View all jobs for a class or school
- History: Complete production history per student

File Associations

- Source files: Original documents
- Working files: Intermediate versions
- Output files: Final deliverables
- Reference files: Supporting documents

Metadata

All jobs support:

- Dublin Core: Standard metadata fields
- Custom Fields: Organization-specific metadata
- Tags: Categorization and filtering

## 📊 Workflow Comparison

| Feature | Braille | Large Print | eBraille | EPUB/DAISY | Tactile Graphics | 3-D Print |
| --- | --- | --- | --- | --- | --- | --- |
| Typical Steps | 8-12 | 6-10 | 5-8 | 10-15 | 12-20 | 3-5 |
| QA Tools | LibLouis, BRLTTY | - | - | DAISY Ace, EPUBCheck | - | - |
| File Types | .brf, .brl | .pdf, .docx | .brf | .epub, .html | .svg, .png | .stl, .gcode |
| Special Equipment | Braille embosser | Large format printer | - | - | Thermoform machine | 3D printer |
| Consumables | Braille paper | Large print paper | - | - | Thermoplastic | Filament |
| Avg. Turnaround | 3-5 days | 2-3 days | 1-2 days | 4-7 days | 5-10 days | 1-3 days |



