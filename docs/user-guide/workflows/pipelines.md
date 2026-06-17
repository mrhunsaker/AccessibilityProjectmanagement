# Workflow Pipelines

Navigate to **QA & Automation → Pipelines** to execute multi-step
accessibility production pipelines.

---

## 📋 Built-in Pipelines

### DAISY Pipeline

Runs DAISY Pipeline 2 tasks for EPUB/DAISY processing.

| Step | Tool | Command |
|------|------|---------|
| List Available Scripts | DAISY Pipeline | `pipeline2-cli scripts` |
| Convert EPUB to DAISY | DAISY Pipeline | `pipeline2-cli run --script epub3-to-daisy ...` |

**Requires**: `pipeline2-cli` on PATH.
Install: <https://daisy.org/pipeline>

---

### Accessible EPUB Pipeline

Converts a document to EPUB and validates it for accessibility.

| Step | Tool | Command |
|------|------|---------|
| Convert Document | Pandoc | `pandoc {input} -o output.epub` |
| Validate EPUB Structure | EPUBCheck | `epubcheck output.epub` |
| Accessibility QA | DAISY Ace | `ace output.epub -o ace-report` |

**Requires**: `pandoc`, `epubcheck`, `ace` on PATH.

---

### Braille Production Pipeline

Translates a text document to Braille.

| Step | Tool | Command |
|------|------|---------|
| Translate Braille | Liblouis | `file2brl {input}` |
| Braille Device QA | BRLTTY | `brltty --help` |

**Requires**: `file2brl`, `brltty` on PATH.

---

## ▶️ Executing a Pipeline

1. Click **▶ Execute Pipeline** on the pipeline card.
2. Optionally enter an **Input File Path** (required for conversion steps).
3. Click **Execute**.
4. Results appear below the pipeline list, showing per-step pass/fail and
   any output.

---

## 📋 Pipeline History

Click **📋 View History** to see the most recent 20 runs for that pipeline.
Each run shows status (completed / failed), start and finish timestamps, and
per-step results.

All pipeline runs are also stored in the `pipeline_run` and
`pipeline_step_run` tables and visible in **Recent Pipeline Runs** at the
bottom of the Pipelines page.

---

## 🔒 Binary Pre-Check

Before executing each step, APM checks that the `required_binary` exists via
`shutil.which()`.  If the binary is missing, the step is marked as failed
with a clear "not found on PATH — install the tool" message, and the
remaining steps still run so all results are recorded.

---

## ➕ Adding Custom Pipelines

See [Custom Workflows](../../development/custom-workflows.md) for
instructions on adding pipelines in code.
