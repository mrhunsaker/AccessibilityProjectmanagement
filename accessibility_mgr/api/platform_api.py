"""REST API foundation layer.

Provides initial API endpoints for:
- workflow execution
- governance inspection
- analytics retrieval
- QA visibility
"""

from __future__ import annotations

import os

from fastapi import Depends, FastAPI, Header, HTTPException, status

from ..services.singletons import analytics as _analytics
from ..services.singletons import auth as _auth
from ..services.singletons import provenance as _provenance
from ..services.singletons import queue as _queue


app = FastAPI(
    title="Accessibility Operations API",
    version="0.1.0",
)

_require_api_key = os.getenv("ACCESSMAN_API_AUTH_REQUIRED", "1").lower() not in {
    "0", "false", "no", "off"
}
_configured_api_key = os.getenv("ACCESSMAN_API_KEY", "").strip()
if _configured_api_key:
    _auth.register_api_token(
        owner="configured-api-user",
        raw_token=_configured_api_key,
        expiration_hours=24 * 365,  # 1-year maximum; rotate via environment variable.
    )


def _require_api_auth(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    if not _require_api_key:
        return
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )
    if not _auth.validate_token(x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


@app.get("/health")
def healthcheck() -> dict:
    return {
        "status": "ok",
        "service": "accessibility-operations-api",
    }


@app.get("/workflows")
def list_workflows(_: None = Depends(_require_api_auth)) -> dict:
    return {
        "jobs": _queue.list_jobs(),
    }


@app.post("/workflows/enqueue")
def enqueue_workflow(
    workflow_name: str,
    asset_id: int,
    priority: int = 5,
    _: None = Depends(_require_api_auth),
) -> dict:
    job = _queue.enqueue(
        workflow_name=workflow_name,
        asset_id=asset_id,
        priority=priority,
    )

    return {
        "workflow": workflow_name,
        "asset_id": asset_id,
        "status": job.status,
    }


@app.get("/analytics")
def analytics_summary(_: None = Depends(_require_api_auth)) -> dict:
    return _analytics.summarize()


@app.get("/provenance")
def provenance_events(_: None = Depends(_require_api_auth)) -> dict:
    return {
        "events": _provenance.list_events(),
    }
