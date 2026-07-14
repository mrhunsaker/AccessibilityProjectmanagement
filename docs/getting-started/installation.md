# Installation Guide

**Step-by-step instructions to install and set up Accessibility Project Management.**

---

## Prerequisites

### Supported Operating Systems
- **Linux** (Ubuntu 22.04+, Fedora 38+, Arch Linux)
- **macOS** (12 Monterey+)
- **Windows** (10 21H2+, 11)

### Required Software

| Requirement | Version | Verification Command |
|-------------|---------|---------------------|
| **Python** | >= 3.12 | `python --version` |
| **[uv](https://github.com/astral-sh/uv)** | Latest | `uv --version` |
| **Git** | >= 2.30 | `git --version` |

---

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/mrhunsaker/AccessibilityProjectManagement.git
cd AccessibilityProjectManagement
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Configure Secrets

Create a `.secrets` file in the **repository root** (not inside `accessibility_mgr/`):

```bash
touch .secrets
chmod 600 .secrets
```

#### Generate Required Secrets

Storage Secret:

```bash
python -c "import secrets; print('STORAGE_SECRET=' + secrets.token_urlsafe(32))" >> .secrets
```

Password Hash (PBKDF2-HMAC-SHA-256):

```bash
python -c "
import hashlib, os, base64
password = b'your_password_here'
salt = os.urandom(16)
dk = hashlib.pbkdf2_hmac('sha256', password, salt, 260000)
print('ACCESSMAN_PASSWORD_HASH=' + base64.b64encode(salt + dk).decode())
" >> .secrets
```

### 4. Configure External Tools (Optional)

```bash
cp tools.ini.example tools.ini
```

Edit `tools.ini` to specify paths to your external tools.

### 5. Run the Application

```bash
uv run AccessMan
```

Open your browser to [http://localhost:8765](http://localhost:8765)

### Troubleshooting

| Issue | Solution |
| --- | --- |
| ModuleNotFoundError | Run `uv sync` |
| FileNotFoundError: .secrets | Create `.secrets` in repository root |
| ValueError: Storage secret is missing | Add `STORAGE_SECRET` to `.secrets` |
| Port 8765 already in use | Change port in `app.py` |
