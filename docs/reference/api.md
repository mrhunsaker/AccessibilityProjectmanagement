# API Reference

This section documents the API-layer modules and their callable interfaces.
Focus is on what each module does in runtime flow: token registration, request
handling, and service exposure.

## Package entrypoint

Purpose: package export boundary for API components.

::: accessibility_mgr.api

## Platform API

Purpose: mounted FastAPI routes, auth/token checks, and externally reachable
workflow/analytics endpoints.

::: accessibility_mgr.api.platform_api
