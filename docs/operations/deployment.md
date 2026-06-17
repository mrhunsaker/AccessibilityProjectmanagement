# Deployment

APM is designed for **single-workstation local deployment**.  The sections
below cover production-hardening steps for studio or shared-office use.

---

## 🖥️ Standard Local Deployment

```bash
git clone https://github.com/mrhunsaker/AccessibilityProjectManagement.git
cd AccessibilityProjectManagement
uv sync
# create .secrets (see Installation guide)
uv run AccessMan
```

APM binds to `localhost:8765` by default.  To expose it on a LAN:

```python
# app.py – change the ui.run() call
ui.run(host="0.0.0.0", port=8765, ...)
```

> **Warning**: Exposing on `0.0.0.0` without a reverse proxy and TLS is only
> appropriate on a trusted internal network.

---

## 🔄 systemd Service (Linux)

```ini
# /etc/systemd/system/accessibility-mgr.service
[Unit]
Description=Accessibility Project Manager
After=network.target

[Service]
Type=simple
User=studio
WorkingDirectory=/opt/accessibility-mgr
EnvironmentFile=/opt/accessibility-mgr/.secrets
ExecStart=/opt/accessibility-mgr/.venv/bin/python -m accessibility_mgr.app
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now accessibility-mgr
```

---

## 🪟 Windows Task Scheduler

1. Open **Task Scheduler** → **Create Task**.
2. **Trigger**: At log on (for the studio user account).
3. **Action**: Start a program → `uv.exe` → arguments: `run AccessMan`.
4. **Start in**: repository root.
5. Set `.secrets` variables in the task **Environment Variables** section.

The `run.bat` launcher in the repository root provides a double-click shortcut.

---

## 🔀 Reverse Proxy (nginx)

For HTTPS access:

```nginx
server {
    listen 443 ssl;
    server_name apm.studio.local;

    ssl_certificate     /etc/ssl/certs/apm.crt;
    ssl_certificate_key /etc/ssl/private/apm.key;

    location / {
        proxy_pass http://127.0.0.1:8765;
        proxy_set_header Host $host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
```

WebSocket upgrade headers are required for NiceGUI's real-time updates.

---

## 📦 Data Directory

The database, artifact store, and backups all live under:

```
~/.local/share/accessibility_mgr/
├── accessibility_manager.db
├── artifacts/
├── job_files/
├── prints_files/
└── backups/
```

Override with `ACCESSMAN_DB_PATH` to store data on a separate drive.
