# Fixes Applied — AccessibilityProjectmanagement

Companion to `AUDIT_REPORT.md`. Maps each numbered problem to what was actually
changed, with the exact files touched. All changes were verified with
`py_compile` across the whole package, the existing `tests/test_queries.py`
suite, direct unit tests of the new/changed logic, and a real boot of the
NiceGUI app (HTTP 200 on `/`, all pages registering with zero failures).

One correction to the original audit along the way: `toolchain_dashboard.py`,
`qa_dashboard.py`, `binary_integrations_dashboard.py`, `cicd_dashboard.py`, and
`workflow_monitor.py` were **not actually reachable from the app's navigation
menu** — `app.py` keeps an explicit `PAGE_DEFINITIONS` list, and none of these
five pages were in it. They were live, callable, fully wired Python — just
orphaned from the UI a real user would click through. That lowers the
real-world exposure of Problems 1 and 2 versus how the original report
described them, but doesn't change that the underlying logic was fake — and
several of these pages are now fixed *and* registered, so they're reachable
and correct going forward.

---

## Critical

### Problem 1 — Fake "passed" toolchain dashboard result — **Fixed**
- Removed `run_mock_ace()` / `run_mock_epubcheck()` from
  `services/toolchain.py` entirely.
- Deleted `ui/toolchain_dashboard.py` (the page these fed) rather than
  rebuilding a third redundant tool-runner UI — `ui/qa.py` (already
  registered, already real) covers running these tools, and
  `ui/binary_integrations_dashboard.py` covers binary-availability status.
- Registered the real, already-correct `ui/binary_integrations_dashboard.py`
  in `app.py` navigation as **"Toolchain Status"** (it previously existed but
  was orphaned from the nav).

### Problem 2 — Self-documented simulated Ace check — **Fixed**
- `services/epub_qa.py`'s `run_ace_check()` now calls the real
  `AccessibilityBinaryIntegrationService.run_daisy_ace()` instead of scoring
  based on the filename string. Handles three honest failure paths
  (file not found / wrong extension / Ace not installed) plus a best-effort
  parser for Ace's `report.json` that doesn't assume one exact schema.
- Deleted `services/qa_persistence.py` (in-memory, name implied durability)
  and replaced the page's persistence with real database rows.
- Added a `qa_measure` table (`db/schema.py`) and
  `log_qa_measure()` / `list_qa_measures()` (`db/queries.py`), including a
  link to a job's event log (`QA_MEASURE_SUBMITTED`) when a job is specified.
- Rebuilt `ui/qa_dashboard.py`: real EPUB path input → runs Ace for real →
  opens a popup form pre-filled with the detected score/pass-fail/issues →
  reviewer can confirm or override before submitting to the database → a
  live "Submitted QA Measures" table below reads back from the database.
- Registered as **"EPUB QA Review"** in `app.py` navigation.

### Problem 3 — CI/CD gate never checked the tool's actual result — **Fixed**
- `integrations/cicd_hooks.py`'s `validate_epub_pipeline()` now reads the
  real exit code from both Ace and EPUBCheck. Branches: tool not installed →
  `"warning"`; either tool's exit code is non-zero → `"failed"`; both clean →
  `"passed"`. Unit-tested all four branches directly.

---

## High

### Problem 4 — In-memory, self-seeded "Enterprise" layer — **Partially addressed**
- The workflow queue, analytics, and provenance registry are now genuinely
  SQLite-backed (see Problem 7) and wired into the shared singletons used by
  both the REST API and the UI.
- Fixed two "private instance instead of shared singleton" bugs found while
  doing this:
  - `ui/workflow_monitor.py` was creating its own `WorkflowQueueService()`
    instead of importing the shared one, so jobs enqueued via the REST API
    were invisible to it (and vice versa) — directly contradicting
    `singletons.py`'s own documented guarantee. Now imports
    `services.singletons.queue`.
  - `ui/operations_dashboard.py` now uses the shared, persistent
    `services.singletons.analytics` instead of a private `AnalyticsService()`.
- Registered the now-correctly-wired `ui/workflow_monitor.py` as
  **"Workflow Monitor"** in navigation.
- **Not done:** `sla_monitoring.py`, `workflow_dag.py`, `multi_tenant.py`,
  `artifact_retention.py`, `audit_log.py`, `distributed_workers.py`, and
  `event_stream.py` are still in-memory only, and `operations_dashboard.py`
  still seeds them with demo data on first load. Converting all seven to
  real persistence tied to genuine domain events (job creation/completion,
  real worker processes, real SLA deadlines from job due dates) is a larger
  product/architecture decision than a bug-fix pass — flagging for a
  follow-up rather than guessing at the intended design.

### Problem 5 — Unkeyed hash labeled a "signature" — **Fixed**
- `services/compliance_reporting.py`: `_sign_payload()` now returns real
  HMAC-SHA256 (verifiable, proves authenticity) when `ACCESSMAN_SIGNING_KEY`
  is configured. With no key configured, it falls back to a SHA-256
  checksum but labels it `"SHA256-CHECKSUM-UNSIGNED"` instead of calling it
  signed.
- Added `verify_signature()`. Tested: correct key verifies, wrong key
  fails, tampered payload fails, checksum mode correctly identified as
  unsigned.

---

## Medium

### Problem 6 — Dead/orphaned modules — **Partially addressed**
- `services/production_toolchain.py`, `services/persistent_queue.py`, and
  `services/toolchain_security.py` were dead. `persistent_queue.py` is now
  live (wired into `singletons.py`, see Problem 7). The other two
  (`production_toolchain.py`, `toolchain_security.py`) remain unused —
  `services/toolchain_binaries.py` (already used by two other live call
  sites) was the more consistent choice to standardize on rather than
  introducing a third overlapping toolchain implementation. Recommend
  deleting `production_toolchain.py` / `toolchain_security.py` in a follow-up
  if no other use is planned for them.
- `api/rest_api.py` (`AccessibilityPlatformAPI`), `models/assets.py`,
  `models/inventory.py`, `db/database.py` (legacy ORM layer),
  `services/resource_monitor.py`, `services/secrets_service.py`,
  `services/subprocess_sandbox.py`, `services/notification_service.py`,
  `services/preservation_service.py`, `services/metadata_schema_service.py`,
  `services/workflow_dependencies.py`, and `security/tenant_rbac.py` are
  still unused. Left as-is rather than guessing at integration points that
  weren't part of the audit's scope.

### Problem 7 — "Persistent" services were plain in-memory objects — **Fixed**
- `services/persistent_analytics.py` (`PersistentAnalyticsService`):
  rewritten with a real `analytics_metric` SQLite table — `record_metric`,
  `summarize`, `list_metrics` all read/write the database.
- `services/persistent_provenance.py` (`PersistentProvenanceRegistry`):
  rewritten with a real `provenance_event` SQLite table.
- `services/persistent_queue.py` (`PersistentWorkflowQueue`): given full
  method parity with `WorkflowQueueService` (`next_job` / `complete_job` /
  `fail_job`, not just `enqueue`/`dequeue`/`list_jobs`) so it can be a
  drop-in replacement, and `services/worker_runtime.py`'s type hint relaxed
  to a duck-typed `Protocol` so it accepts either implementation.
- `services/singletons.py` now constructs all three from these real
  implementations. Verified data survives a fresh process (separate Python
  invocation, same DB file) for all three.
- `services/qa_persistence.py` was the third "Persistence"-named in-memory
  class; deleted as part of the Problem 2 fix once real DB-backed measures
  replaced it.

### Problem 8 — Stale duplicate root file — **Fixed**
- Deleted `students.py` (repo root).

---

## Low

### Problem 9 — Import-time filesystem side effect — **Fixed**
- `services/secrets_service.py`: directory creation/chmod moved from
  module level into a helper called only from `save_secret()`. Verified
  importing the module no longer creates a directory; `save_secret`/
  `load_secrets` still work correctly when actually used.

### Problem 10 — `ui.row()` not used as a context manager — **Fixed**
- `ui/binary_integrations_dashboard.py`: wrapped in `with ui.row():` so the
  icon/label are actually nested inside it. Also added a third Liblouis
  status tile while in this file, since `toolchain_binaries.py` already
  supports it but the page only checked two of the three tools.

### Problem 11 — Leftover `.back`/`.back2` files — **Fixed**
- Deleted `security/authentication.py.back`, `services/tools_service.py.back`,
  `tests/test_queries.py.back`, `tests/test_queries.py.back2`.

---

---

## Follow-up pass — additional stub-equivalent code found and fixed

A second targeted search (grepping for "sample/demo/fake/mock/simulated/
hardcoded/echo" patterns repo-wide, then manually inspecting each hit)
turned up four more cases of the same pattern as the original report:
code that runs without error and looks complete, but either fabricates a
result instead of doing real work, or has no way to actually submit real
data. All four are now fixed, each replacing the fake/static behavior with
a real tool call or form that submits to the database.

### ANZAGG Validation tool secretly always "passed" — Fixed
**Location:** `services/qa_service.py` (`QA_TOOLS` list, `QAService.run_tool`)

The "ANZAGG Validation" QA tool (tactile/3D accessibility review) was
configured with `executable="echo"` and
`command_template="echo ANZAGG validation requires manual tactile review of: {input}"`.
Clicking "Run Validation" in `ui/qa.py` executed `echo`, which always exits
0, so `QAService.run_tool` always logged `success=True` to the `qa_run`
table and to the job's event log — a tactile graphic could show as a
**passed** accessibility review despite no human ever looking at it.

Fixed by adding a `manual_review: bool` field to `QATool`. ANZAGG is now
defined with `executable=""`, `manual_review=True`, and `run_tool()`
refuses to execute it (returns an honest error pointing at the review
form instead of running anything). Added
`QAService.log_manual_qa_review()`, which writes a real `qa_run` row from
actual reviewer-submitted data. `ui/qa.py` now detects `manual_review`
tools and opens a **"Record Manual Review"** popup form (reviewer name,
pass/fail switch, free-text findings, optional job link) instead of the
normal run dialog — submitting it calls the new service method and
displays the real recorded result. Tested end-to-end including the
job-event-log link.

### Operations Dashboard wrote fake metrics into the real database on every load — Fixed (now worse-than-before bug, caused by the earlier persistence fix)
**Location:** `ui/operations_dashboard.py` (`_seed_once()`)

This function pre-existed as a demo-data seeder against the (then)
in-memory analytics service. After the earlier persistence fix
(`PersistentAnalyticsService` → real SQLite), this same function started
writing a fabricated `qa_accessibility_score: 98` metric and two other
fake KPIs into the **real, persistent** database every time a user loaded
the page (`if _seeded` only guarded against re-seeding within one process
run, not across restarts) — meaning the production analytics history
would accumulate fabricated entries indistinguishable from real ones.

Fixed by deleting `_seed_once()` entirely, along with the fake DAG/worker/
event-subscription/SLA registrations it performed. The dashboard now opens
genuinely empty (verified: `list_organizations()` / `list_nodes()` return
`[]` on a fresh database) until real data is added through the forms below.

### Three operations-dashboard buttons that fabricated data instead of collecting it — Fixed
**Location:** `ui/operations_dashboard.py`

Three buttons performed an action using auto-generated placeholder
values with no user input:
- **"Add Sample Organization"** — created `Organization {idx}` with member
  `operator{idx}`, no real org name or username ever entered.
- **"Register Worker"** — registered `worker-{idx}` at `host-{idx}`, never
  a real node ID or hostname.
- **"Publish Test Event"** — always published a hardcoded
  `{"status": "ok", "sequence": N}` payload under a hardcoded
  `event_type="workflow_status"`.
- ("Register Artifact" had a related issue: it wrote a throwaway
  `.tmp` file to disk just to have *something* to register, rather than
  taking a path to a real artifact.)

All four are now real form dialogs (Add Organization, Register Worker,
Publish Event, Register Artifact) that collect actual required fields
(organization name + initial member/role, node ID + hostname, event type +
JSON payload, artifact path + retention days), validate them, and only
then call the underlying service — consistent with the popup-form +
database-submission pattern used for Problem 2's QA measures. Verified
the create-organization path end-to-end against a live service instance.

### CI/CD dashboard had no way to trigger a validation, and history was wiped on restart — Fixed
**Location:** `ui/cicd_dashboard.py`, `integrations/cicd_hooks.py`,
new `cicd_validation_run` table

The page was a static read-only checklist ("DAISY Ace pipeline validation",
"Continuous accessibility governance", etc., all rendered as permanently
green checkmarks) plus a history list that nothing in the app ever
populated, because `CICDValidationHookService._history` was a private
in-memory list and the page had no button to call
`validate_epub_pipeline()` at all.

Rewrote the page with a real **"Run Validation"** form (pipeline ID +
EPUB path) that calls the real CI/CD gate (the one already fixed for
Problem 3) and displays the actual pass/fail/warning result with each
tool's real exit code. Added a `cicd_validation_run` table
(`db/schema.py`) and `log_cicd_validation_run()` /
`list_cicd_validation_runs()` (`db/queries.py`); `CICDValidationHookService`
now persists every run there instead of an in-memory list, so history
survives a restart — verified by creating a fresh service instance after
a run and confirming the history is still visible (mirroring the same
restart-persistence test used for Problem 7). The page was also registered
in `app.py` navigation as **"CI/CD Validation"**, since (per the earlier
audit) it was never reachable from the menu to begin with.

### Verification (this pass)
- `py_compile` across the whole package: clean.
- `pytest tests/test_queries.py`: 12 passed, same 1 pre-existing unrelated
  failure as before.
- Direct functional tests run for all four fixes: ANZAGG's `is_available()`
  /`run_tool()` refusal / `log_manual_qa_review()` + job-event-log link;
  CI/CD history surviving a fresh service instance; operations dashboard
  cold-starting empty and the real organization-creation path working.
- Full app boot (`python -m accessibility_mgr.app`): HTTP 200 on `/`, all
  25 pages registered, zero failures.

---

## Verification summary (first pass)

- `python -m py_compile` across every `.py` file in `accessibility_mgr/`:
  clean.
- `pytest tests/test_queries.py`: 12 passed, 1 pre-existing failure
  unrelated to any of these changes (confirmed by reproducing it against an
  unmodified checkout — a tmpdir-path assumption in the test itself).
- Direct unit tests written and run (not committed as test files, run
  ad hoc) for: `epub_qa.run_ace_check()`'s three honest-failure paths,
  `cicd_hooks.validate_epub_pipeline()`'s four status branches,
  `log_qa_measure`/`list_qa_measures` including the job-event-log link,
  `compliance_reporting`'s HMAC vs. checksum modes and tamper detection,
  and restart-persistence for the queue/analytics/provenance SQLite tables.
- A real boot of the app (`python -m accessibility_mgr.app`) served the
  homepage over HTTP with all 24 pages registered and zero failures, and the
  resulting SQLite file contained all four new tables
  (`qa_measure`, `workflow_queue`, `analytics_metric`, `provenance_event`)
  alongside the existing domain tables.
