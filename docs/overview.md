# Overview

This project is organized into a small number of layers so that the UI, data access, and workflow logic stay easy to document and maintain.

## Application layer

[`accessibility_mgr.app`](reference/app.md) is the NiceGUI entrypoint. It registers the page handlers, boots the database, configures the UI favicon, and starts the server.

## Data layer

[`accessibility_mgr.db.schema`](reference/database.md) owns schema creation and database bootstrap behavior. [`accessibility_mgr.db.queries`](reference/database.md) holds the SQL data-access API used by the UI and services.

## Services layer

[`accessibility_mgr.services.workflow_engine`](reference/services.md) contains legacy workflow validation helpers. [`accessibility_mgr.services.tools_service`](reference/services.md) normalizes external command paths for docs, validation, and accessibility tooling.

## UI layer

The pages under [`accessibility_mgr.ui`](reference/ui.md) implement the dashboard, inventory management, production workflows, search, metadata editing, QA, and administration screens.

## Legacy data models

The SQLAlchemy models in [`accessibility_mgr.models`](reference/models.md) are still documented for compatibility and future migration work.
