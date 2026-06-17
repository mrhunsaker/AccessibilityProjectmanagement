# Extending APM

APM does not have a formal plugin system, but each layer has well-defined
extension points.

---

## 📄 Adding a New UI Page

1. Create `accessibility_mgr/ui/my_page.py` with a function `my_page(content_area)`.
2. Add an entry to `PAGE_DEFINITIONS` in `accessibility_mgr/app.py`:

```python
{
    "name": "My Page",
    "icon": "star",                         # Material Icons name
    "module": "accessibility_mgr.ui.my_page",
    "function": "my_page",
    "description": "Short description",
    "group": "Overview",                    # Sidebar group
},
```

The page will appear in the sidebar automatically on the next restart.

---

## 🔧 Adding a QA Tool

Add a `QATool` entry to `QA_TOOLS` in `services/qa_service.py`:

```python
QATool(
    name="My Validator",
    domain="Custom QA",
    description="Validates custom accessibility format",
    executable="my-validator",
    command_template="my-validator {input} --report",
    timeout=60,
),
```

Also add `"my-validator"` to `ALLOWED_EXECUTABLES` in
`services/execution_service.py`.

---

## 🔗 Adding a Pipeline

See [Custom Workflows](custom-workflows.md) for full instructions.

---

## 📊 Adding Analytics Metrics

Call `AnalyticsService.record_metric()` from any service or page:

```python
from accessibility_mgr.services.singletons import analytics

analytics.record_metric(
    metric_name="my_kpi",
    metric_value=42.0,
    category="production",
    metadata={"job_type": "braille"},
)
```

Metrics are visible in the Operations Dashboard summary.

---

## 🌐 Adding REST Endpoints

Mount additional FastAPI routes on the `app` object in
`api/platform_api.py`:

```python
@app.get("/my-endpoint")
def my_endpoint(_: None = Depends(_require_api_auth)) -> dict:
    return {"data": "example"}
```

The FastAPI app is mounted at `/api`, so the full URL is
`http://localhost:8765/api/my-endpoint`.
