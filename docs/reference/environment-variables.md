# Environment Variables Reference

## 🔐 Authentication & Security
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `STORAGE_SECRET` | Yes | - | NiceGUI session encryption key |
| `ACCESSMAN_PASSWORD_HASH` | Yes | - | PBKDF2 password hash for login |
| `ACCESSMAN_VAULT_KEY` | Yes | - | Fernet key for encrypted secrets |
| `ACCESSMAN_API_AUTH_REQUIRED` | No | `0` | Enable API authentication (`1` = yes) |
| `ACCESSMAN_API_KEY` | No | - | API key for authentication |
| `ACCESSMAN_UNPROTECTED` | No | `0` | **Danger:** Disable auth for dev (`1` = yes) |

## 🗃️ Database & Storage
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ACCESSMAN_DB_PATH` | No | User data dir | SQLite database path |
| `ACCESSMAN_BACKUP_DIR` | No | `backups/` | Backup directory |
| `ACCESSMAN_BACKUP_RETENTION` | No | `30` | Backup retention count |

## 📊 Logging
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ACCESSMAN_LOG_LEVEL` | No | `INFO` | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---
## 🔑 Generating Secrets

### Storage Secret
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Password Hash (PBKF2)

```bash
python -c "
import hashlib, os, base64
salt = os.urandom(16)
dk = hashlib.pbkdf2_hmac('sha256', b'your_password', salt, 260000)
print(base64.b64encode(salt + dk).decode())
"
```

### Fernet Vault Key

``bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### API Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```
