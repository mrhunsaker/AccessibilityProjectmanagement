# CHANGES

All notable project changes should be documented in this file.

The format loosely follows Keep a Changelog principles.

---

# 2026-05-17

## Added

### Enterprise Workflow Orchestration
- Persistent SQLite-backed workflow queue
- Workflow DAG orchestration engine
- Workflow dependency resolution
- Workflow replay and recovery engine
- Distributed reconciliation service
- Worker heartbeat monitoring
- Worker failover detection
- SLA monitoring infrastructure
- Distributed worker registry

### Accessibility Automation
- Production DAISY Ace binary integration
- Production EPUBCheck integration
- Secure subprocess sandboxing layer
- Accessibility toolchain telemetry
- Artifact capture orchestration
- Timeout-controlled binary execution
- Binary integration monitoring dashboard

### CI/CD Accessibility Governance
- GitHub Actions accessibility validation workflow
- CI/CD accessibility validation orchestration
- Accessibility severity-threshold policy engine
- Release-blocking governance enforcement
- Automated EPUB accessibility validation
- Pipeline execution telemetry
- CI/CD governance dashboard

### Security and Identity
- Tenant-aware RBAC enforcement
- Authentication middleware
- API token validation
- Credential vault abstraction
- Permission evaluation engine
- Multi-tenant organization infrastructure
- Tenant membership management

### Reliability Infrastructure
- Webhook retry engine
- Dead-letter queue support
- Persistent event store
- Signed event persistence
- Artifact retention lifecycle management
- Automated artifact cleanup
- Distributed orchestration telemetry

### Governance and Compliance
- Operational provenance registry
- Audit-grade event tracking
- Governance workflow telemetry
- Compliance-oriented workflow orchestration
- Operational analytics persistence

## Changed

- Expanded repository architecture from NiceGUI workflow application into enterprise accessibility governance platform
- Transitioned orchestration layer from in-memory execution to durable distributed workflow infrastructure
- Transitioned accessibility tooling from execution stubs to production binary integration model
- Expanded CI/CD support into deployable accessibility governance automation
- Expanded RBAC implementation into tenant-aware authorization model
- Expanded operational telemetry into audit-grade event persistence architecture
- Expanded reliability infrastructure with replay/recovery semantics and distributed reconciliation

## Planned

- Real encrypted KMS/HSM-backed secret storage
- Queue partitioning and distributed workload balancing
- Tenant-aware API authorization middleware
- Signed governance export generation
- Immutable compliance snapshot exports
- Workflow auto-remediation routing
- Adaptive orchestration retry policies
- Distributed auto-scaling workers

---

# 2026-05-09

## Added

- Initial NiceGUI application shell
- Dynamic page loading for UI modules
- Sidebar-based navigation
- Responsive content layout
- Dashboard integration
- Graceful handling for incomplete UI modules
- Application-wide color/theme configuration
- Header/status display components
- Architecture and workflow audit documentation
- LLM remediation prompt specification (`prompt.json`)
- Asset Registry NiceGUI page
- Metadata workflow visibility dashboard
- METS-inspired asset management concepts
- Metadata lineage planning documentation

## Changed

- Replaced placeholder `app.py` implementation with a functional NiceGUI frontend
- Updated project documentation to reflect current architecture
- Updated README to document NiceGUI migration strategy
- Updated repository structure documentation
- Clarified technology stack and workflow functionality
- Expanded application shell to include metadata-oriented workflows
- Expanded project scope toward preservation-oriented accessibility production

## Planned

- Full migration from Textual TUI to NiceGUI
- CRUD interfaces for all production workflows
- Reporting and analytics
- Authentication support
- Accessibility auditing improvements
- Multi-user operation support
- Full metadata lineage tracking
- Asset version graph visualization
- Preservation export tooling
- Workflow automation pipelines
