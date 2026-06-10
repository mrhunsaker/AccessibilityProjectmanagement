# Overview

This project is organized into a small number of layers so that the UI, data access, and workflow logic stay easy to document and maintain.

## Application layer

[`accessibility_mgr.app`](reference/app.md) is the NiceGUI entrypoint. It registers the page handlers, mounts the FastAPI API under `/api`, boots the database, configures the UI favicon, and starts the server.

## Data layer

[`accessibility_mgr.db.schema`](reference/database.md) owns schema creation and database bootstrap behavior. [`accessibility_mgr.db.queries`](reference/database.md) holds the SQL data-access API used by the UI and services.

The data layer also defines lookup categories and metadata option sets used by
inventory, metadata editing, and workflow UIs.

## Services layer

[`accessibility_mgr.services.authentication`](reference/services.md) provides the token registry used by the mounted API. [`accessibility_mgr.services.tools_service`](reference/services.md) normalizes external command paths for docs, validation, and accessibility tooling.

Pipeline orchestration is handled by the pipeline services; DAISY Pipeline is
registered in the Pipelines domain rather than QA Tooling.

## UI layer

The pages under [`accessibility_mgr.ui`](reference/ui.md) implement the dashboard, inventory management, production workflows, search, metadata editing, QA, administration screens, and the shared quick-create / bulk-action UX.

Recent UI behavior includes:

- Artifact-targeted ingestion forms using project metadata.
- Controlled metadata editing with governed options and examples.
- EPUB3/DAISY job flows under production pages.
- Electronics inventory category rendering for both populated and empty
  categories, including inline category creation support.
- Dashboard quick navigation, upcoming deadline visibility, and overdue due-date highlighting.

## Legacy data models

The SQLAlchemy models in [`accessibility_mgr.models`](reference/models.md) are still documented for compatibility and future migration work.
