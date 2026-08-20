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

The interactive setup assistant handles this automatically when you first
launch the application.  You can also run it manually:

**Linux / macOS:**

```bash
./setup.sh
```

**Windows:**

Double-click `setup.bat` in File Explorer, or run:

```cmd
setup.bat
```

**All platforms:**

```bash
python setup.py
```

The assistant will generate `STORAGE_SECRET`, prompt you for an admin
password, create the `.secrets` file, and set appropriate file permissions.

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
| FileNotFoundError: .secrets | Run `python setup.py` to create it |
| ValueError: Storage secret is missing | Add `STORAGE_SECRET` to `.secrets` |
| Port 8765 already in use | Change port in `app.py` |
