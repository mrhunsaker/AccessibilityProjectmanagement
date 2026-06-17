# Custom Workflows & Pipelines

APM supports two levels of workflow customisation: **step configuration** via
the Admin UI and **pipeline definition** in Python.

---

## ⚙️ Configuring Workflow Steps

Default steps are seeded for each job type.  Additional steps can be added via
**Admin → Workflow Steps**:

1. Select a **Job Type** (`braille`, `lp_ebraille`, `tactile`, `print`).
2. Enter a **Step Key** (snake_case, e.g. `proofread2`).
3. Enter a **Label** and optional **Description**.
4. Set a **Sort Order**.
5. Click **Save**.

> **Note**: Custom steps added via the Admin UI are stored in the
> `workflow_step` lookup table for display purposes.  To make them
> *functional* (i.e. trackable via `complete_step()`), you must also add the
> key to `_ALLOWED_STEPS` in `db/queries.py` and the corresponding column to
> the job table via a migration.

---

## 🔧 Adding a New Pipeline

Pipelines are defined in `services/pipeline_service.py`:

```python
from accessibility_mgr.services.pipeline_service import PipelineStep, WorkflowPipeline, PIPELINES

PIPELINES.append(
    WorkflowPipeline(
        name="My Custom Pipeline",
        description="Converts DOCX to BRF via LibLouis.",
        steps=[
            PipelineStep(
                name="Convert Document",
                tool="Pandoc",
                command_template="pandoc {input} -o output.txt",
                timeout=60,
                required_binary="pandoc",
            ),
            PipelineStep(
                name="Braille Translation",
                tool="Liblouis",
                command_template="file2brl output.txt output.brf",
                timeout=120,
                required_binary="file2brl",
            ),
        ],
    )
)
```

The pipeline will appear automatically in the **Pipelines** page after the
next page load (or restart).

### `PipelineStep` Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Display name shown in the UI |
| `tool` | str | Tool label (informational) |
| `command_template` | str | Shell command; `{input}` is replaced at runtime |
| `timeout` | int | Seconds before the step is killed |
| `required_binary` | str | Binary checked via `shutil.which()` before running |

---

## 🔒 Binary Allow-List

`ExecutionService` only launches executables in `ALLOWED_EXECUTABLES`
(`services/execution_service.py`).  Add your binary name there before
creating a pipeline step that uses it:

```python
ALLOWED_EXECUTABLES: frozenset[str] = frozenset({
    "ace", "brltty", "epubcheck", "file2brl", "lou_translate",
    "pandoc", "pipeline2", "pipeline2-cli", "which", "where",
    "my_custom_tool",   # <-- add here
})
```
