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

## Metadata validation

Purpose: validation rules for metadata payloads and constraints.

::: accessibility_mgr.services.metadata_validation

## Multi-tenant

Purpose: tenant isolation and tenant-scoped helper operations.

::: accessibility_mgr.services.multi_tenant

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

## Provenance registry

Purpose: provenance event registration and lookup.

::: accessibility_mgr.services.provenance_registry

## QA service

Purpose: QA workflow execution, scoring, and result emission.

::: accessibility_mgr.services.qa_service

## RBAC

Purpose: role-based access control logic and permission checks.

::: accessibility_mgr.services.rbac

## SLA monitoring

Purpose: SLA tracking and breach detection helpers.

::: accessibility_mgr.services.sla_monitoring

## Toolchain core

Purpose: shared toolchain runtime helpers.

::: accessibility_mgr.services.toolchain

## Toolchain binaries

Purpose: discovery and management of external binary dependencies.

::: accessibility_mgr.services.toolchain_binaries

## Tools service

Purpose: tool-path resolution and command helper entrypoints.

::: accessibility_mgr.services.tools_service

## Worker runtime

Purpose: worker lifecycle and task execution runtime.

::: accessibility_mgr.services.worker_runtime

## Workflow DAG

Purpose: DAG representation for workflow steps and dependencies.

::: accessibility_mgr.services.workflow_dag

## Workflow queue

Purpose: workflow job data structures.

::: accessibility_mgr.services.workflow_queue
