# Monitoring

---

## 📊 Built-in Metrics

### Operations Dashboard

Navigate to **Operations** in the sidebar for live operational KPIs:

- **Tracked Metrics** — count of analytics records
- **SLA Breaches** — workflows that exceeded their SLA window
- **Workers Online** — registered background worker nodes
- **Stream Events** — published platform events

### Resource Monitor (`ResourceMonitorService`)

The service collects system metrics on demand using `psutil` (if installed) or
stdlib fallbacks:

| Metric | psutil | stdlib fallback |
|--------|--------|-----------------|
| CPU % | ✅ | ❌ |
| Memory total / available | ✅ | ❌ |
| Disk total / free / used % | ✅ | ✅ (shutil) |
| Process RSS | ✅ | ✅ (/proc/self/status on Linux) |

Usage:

```python
from accessibility_mgr.services.resource_monitor import ResourceMonitorService

monitor = ResourceMonitorService()
snap = monitor.snapshot()
print(snap.disk_free_gb, snap.cpu_percent)

# Low-disk warning
warning = monitor.disk_warning(threshold_gb=1.0)
if warning:
    print(warning)
```

---

## 📋 Audit Log

Every significant action writes to `metadata_event`.  Query recent events:

```bash
sqlite3 ~/.local/share/accessibility_mgr/accessibility_manager.db \
  "SELECT event_datetime, job_type, event_type, agent, detail
   FROM metadata_event
   ORDER BY event_datetime DESC LIMIT 50;"
```

---

## 🔔 Backup Status

The **Admin → Backups** tab shows:
- Scheduler active / stopped
- Number of stored backups
- Most-recent backup path and size
- Full backup log (trigger, status, size, timestamp)

---

## 📝 Application Logs

APM logs to stderr.  Redirect to a file when running as a service:

```bash
uv run AccessMan >> /var/log/accessibility-mgr.log 2>&1
```

Or via systemd journald:

```bash
journalctl -u accessibility-mgr -f
```
