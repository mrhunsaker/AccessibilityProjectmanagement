# Services

The services package contains small orchestration layers used by the UI and
legacy workflow paths. mkdocstrings renders the public classes and functions
from each module below.

## Authentication

::: accessibility_mgr.services.auth_service

## Automation

::: accessibility_mgr.services.automation_service

## Execution

::: accessibility_mgr.services.execution_service

## Metadata schema

::: accessibility_mgr.services.metadata_schema_service

## Pipeline

::: accessibility_mgr.services.pipeline_service

## Preservation

::: accessibility_mgr.services.preservation_service

## Production

::: accessibility_mgr.services.production_service

## QA

::: accessibility_mgr.services.qa_service

## Schema governance

::: accessibility_mgr.services.schema_governance_service

## Secrets

::: accessibility_mgr.services.secrets_service

## Tool path resolution

::: accessibility_mgr.services.tools_service

## Legacy SQLAlchemy-backed services

The following legacy services are intentionally not rendered by mkdocstrings in
the strict docs build, because they require optional SQLAlchemy runtime
dependencies at import time:

- `accessibility_mgr.services.assets_service`
- `accessibility_mgr.services.file_ingestion_service`
- `accessibility_mgr.services.inventory_service`
- `accessibility_mgr.services.package_service`
- `accessibility_mgr.services.search_service`
- `accessibility_mgr.services.workflow_engine`
