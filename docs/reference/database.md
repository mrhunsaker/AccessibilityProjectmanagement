# Database Reference

The database package is responsible for persistent state, schema migration,
query execution, and import/seed workflows.

## Package entrypoint

Purpose: export surface for DB helpers.

::: accessibility_mgr.db

## Schema and migration

Purpose: connection setup, path resolution, schema initialization, and
incremental migration application.

::: accessibility_mgr.db.schema

## Query layer

Purpose: typed CRUD and workflow queries used by UI pages and services.

::: accessibility_mgr.db.queries

## Seed import

Purpose: CSV normalization and controlled import into inventory tables.

::: accessibility_mgr.db.seed_import

## ORM compatibility base

Purpose: legacy SQLAlchemy compatibility for model modules.

::: accessibility_mgr.db.database
