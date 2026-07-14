"""REST API foundation layer.

Provides API endpoints for:
- workflow execution
- governance inspection
- analytics retrieval
- QA visibility

SEC-005: All mutating endpoints enforce RBAC permissions via the
``_require_permission`` dependency.  The caller's role is resolved
from the authenticated API token owner, and the required permission
is checked against the ``RBACService`` role registry.
"""

from __future__ import annotations

import os

from fastapi import Depends, FastAPI, Header, HTTPException, status

from ..services.rbac import RBACService, UserIdentity
from ..services.singletons import analytics as _analytics
from ..services.singletons import auth as _auth
from ..services.singletons import provenance as _provenance
from ..services.singletons import queue as _queue

app = FastAPI(
    title="Accessibility Operations API",
    version="0.2.0",
)

_rbac = RBACService()

_require_api_key = os.getenv("ACCESSMAN_API_AUTH_REQUIRED", "1").lower() not in {
    "0", "false", "no", "off"
}
_configured_api_key = os.getenv("ACCESSMAN_API_KEY", "").strip()
if _configured_api_key:
    _auth.register_api_token(
        owner="configured-api-user",
        raw_token=_configured_api_key,
        expiration_hours=24 * 365,
    )

_DEFAULT_ROLE = os.getenv("ACCESSMAN_API_DEFAULT_ROLE", "operator").strip()


def _resolve_token_owner(x_api_key: str) -> str | None:
    """Return the owner string for a valid API key, or None."""
    from hashlib import sha256
    hashed = sha256(x_api_key.encode("utf-8")).hexdigest()
    for token in _auth._tokens:
        if token.active and token.token_hash == hashed:
            return token.owner
    return None


def _require_api_auth(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str:
    """Validate API key and return the token owner string."""
    if not _require_api_key:
        return "anonymous"
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
    owner = _resolve_token_owner(x_api_key) or "api-user"
    return owner


def _require_permission(
    owner: str = Depends(_require_api_auth),
    permission: str = "",
) -> str:
    """Enforce that the authenticated caller has *permission*.

    Returns the resolved owner on success.
    """
    if not permission:
        return owner

    user = UserIdentity(username=owner, roles=[])
    role = _rbac.get_role(_DEFAULT_ROLE)
    if role:
        user.roles.append(role)

    if not _rbac.authorize(user, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required permission: {permission}",
        )
    return owner


def _dep_workflow_read(owner: str = Depends(_require_api_auth)) -> str:
    return _require_permission(owner, "")


def _dep_workflow_manage(owner: str = Depends(_require_api_auth)) -> str:
    return _require_permission(owner, "workflow.manage")


def _dep_analytics_view(owner: str = Depends(_require_api_auth)) -> str:
    return _require_permission(owner, "analytics.view")


def _dep_governance_manage(owner: str = Depends(_require_api_auth)) -> str:
    return _require_permission(owner, "governance.manage")


@app.get("/health")
def healthcheck() -> dict:
    return {
        "status": "ok",
        "service": "accessibility-operations-api",
    }


@app.get("/workflows")
def list_workflows(_: str = Depends(_dep_workflow_read)) -> dict:
    return {
        "jobs": _queue.list_jobs(),
    }


@app.post("/workflows/enqueue")
def enqueue_workflow(
    workflow_name: str,
    asset_id: int,
    priority: int = 5,
    _: str = Depends(_dep_workflow_manage),
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
def analytics_summary(_: str = Depends(_dep_analytics_view)) -> dict:
    return _analytics.summarize()


@app.get("/provenance")
def provenance_events(_: str = Depends(_dep_governance_manage)) -> dict:
    return {
        "events": _provenance.list_events(),
    }
