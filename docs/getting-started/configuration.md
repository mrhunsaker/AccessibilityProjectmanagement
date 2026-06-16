# Configuration Guide

**Customize APM for your environment and workflows.**

---

## 🔐 Environment Variables

Load from `.secrets` file in repository root.

### Required Variables
| Variable | Description | How to Generate |
|----------|-------------|-----------------|
| `STORAGE_SECRET` | NiceGUI session encryption | `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `ACCESSMAN_PASSWORD_HASH` | PBKDF2 password hash | See [Installation Guide](installation.md) |
| `ACCESSMAN_VAULT_KEY` | Fernet encryption key | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |

### Optional Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `ACCESSMAN_API_AUTH_REQUIRED` | `0` | Enable API authentication (`1` = enabled) |
| `ACCESSMAN_API_KEY` | - | API key for authentication |
| `ACCESSMAN_DB_PATH` | User data dir | Path to SQLite database |
| `ACCESSMAN_BACKUP_DIR` | `backups/` | Backup directory |
| `ACCESSMAN_BACKUP_RETENTION` | `30` | Number of backups to retain |

---
## 📂 External Tool Configuration

Edit `tools.ini`:
```ini
[tools]
ace = /usr/local/bin/ace
epubcheck = /usr/local/bin/epubcheck
pipeline = /opt/daisy-pipeline/bin/pipeline2
liblouis = /usr/bin/lou_translate

[paths]
extra =
    /opt/daisy-pipeline/bin
    /usr/local/share/npm/bin
