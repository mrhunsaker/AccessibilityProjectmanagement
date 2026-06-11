# Services Reference

Services are the orchestration layer between UI interactions, database access,
workflow execution, and operational controls.

## Package entrypoint

Purpose: service package exports.

::: accessibility_mgr.services

## Analytics

Purpose: analytics event collection and reporting helpers.

::: accessibility_mgr.services.analytics

## Artifact retention

Purpose: retention and cleanup policy handling for generated artifacts.

::: accessibility_mgr.services.artifact_retention

## Audit log

Purpose: audit stream normalization and retrieval.

::: accessibility_mgr.services.audit_log

## Authentication

Purpose: user/session authentication workflows and credential validation.

::: accessibility_mgr.services.authentication

## Auth service facade

Purpose: higher-level auth service API used by pages and API endpoints.

::: accessibility_mgr.services.auth_service

## Automation

Purpose: execute scripted operational tasks and automation flows.

::: accessibility_mgr.services.automation_service

## Backup

Purpose: scheduled and on-demand database backups with retention.

::: accessibility_mgr.services.backup_service

## Compliance reporting

Purpose: compliance-oriented summaries and control evidence output.

::: accessibility_mgr.services.compliance_reporting

## Distributed workers

Purpose: worker distribution primitives for asynchronous operations.

::: accessibility_mgr.services.distributed_workers

## EPUB QA

Purpose: EPUB-specific QA checks and result handling.

::: accessibility_mgr.services.epub_qa

## Event stream

Purpose: event bus style stream publication and consumption.

::: accessibility_mgr.services.event_stream

## Execution service

Purpose: controlled command/process execution used by pipeline tasks.

::: accessibility_mgr.services.execution_service

## Metadata audit

Purpose: metadata audit and verification helpers.

::: accessibility_mgr.services.metadata_audit

## Metadata schema

Purpose: metadata schema definitions and validation surface.

::: accessibility_mgr.services.metadata_schema_service

## Metadata validation

Purpose: validation rules for metadata payloads and constraints.

::: accessibility_mgr.services.metadata_validation

## Multi-tenant

Purpose: tenant isolation and tenant-scoped helper operations.

::: accessibility_mgr.services.multi_tenant

## Notifications

Purpose: alert and notification dispatch helpers.

::: accessibility_mgr.services.notification_service

## Persistent analytics

Purpose: durable analytics storage and retrieval.

::: accessibility_mgr.services.persistent_analytics

## Persistent provenance

Purpose: durable provenance registry back-end.

::: accessibility_mgr.services.persistent_provenance

## Persistent queue

Purpose: durable workflow queue persistence and replay.

::: accessibility_mgr.services.persistent_queue

## Pipeline service

Purpose: pipeline orchestration, step flow, and status lifecycle.

::: accessibility_mgr.services.pipeline_service

## Preservation

Purpose: preservation and long-term integrity operations.

::: accessibility_mgr.services.preservation_service

## Production

Purpose: production workflow orchestration and output tracking.

::: accessibility_mgr.services.production_service

## Production toolchain

Purpose: production toolchain integration helpers.

::: accessibility_mgr.services.production_toolchain

## Provenance registry

Purpose: provenance event registration and lookup.

::: accessibility_mgr.services.provenance_registry

## QA persistence

Purpose: persistence support for QA runs and outcomes.

::: accessibility_mgr.services.qa_persistence

## QA service

Purpose: QA workflow execution, scoring, and result emission.

::: accessibility_mgr.services.qa_service

## RBAC

Purpose: role-based access control logic and permission checks.

::: accessibility_mgr.services.rbac

## Schema governance

Purpose: governance checks for schema consistency and policy adherence.

::: accessibility_mgr.services.schema_governance_service

## Secrets service

Purpose: service facade for secret retrieval and secret lifecycle calls.

::: accessibility_mgr.services.secrets_service

## SLA monitoring

Purpose: SLA tracking and breach detection helpers.

::: accessibility_mgr.services.sla_monitoring

## Subprocess sandbox

Purpose: controlled subprocess execution boundaries for safer automation.

::: accessibility_mgr.services.subprocess_sandbox

## Toolchain core

Purpose: shared toolchain runtime helpers.

::: accessibility_mgr.services.toolchain

## Toolchain binaries

Purpose: discovery and management of external binary dependencies.

::: accessibility_mgr.services.toolchain_binaries

## Toolchain security

Purpose: policy and safety checks for toolchain execution.

::: accessibility_mgr.services.toolchain_security

## Tools service

Purpose: tool-path resolution and command helper entrypoints.

::: accessibility_mgr.services.tools_service

## Worker runtime

Purpose: worker lifecycle and task execution runtime.

::: accessibility_mgr.services.worker_runtime

## Workflow DAG

Purpose: DAG representation for workflow steps and dependencies.

::: accessibility_mgr.services.workflow_dag

## Workflow dependencies

Purpose: dependency resolution for workflow scheduling.

::: accessibility_mgr.services.workflow_dependencies

## Workflow queue

Purpose: in-memory queue operations for workflow jobs.

::: accessibility_mgr.services.workflow_queue
