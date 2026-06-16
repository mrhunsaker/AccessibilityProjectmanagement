"""Secrets service — load and persist local authentication secrets.

SEC-006: The secrets directory and file are created with owner-only permissions
(0700 / 0600) so no other OS user can read the stored credentials.
"""
from __future__ import annotations

import json
import os
import stat
from pathlib import Path


SECRETS_DIR = Path("secrets")
SECRETS_DIR.mkdir(exist_ok=True)
# SEC-006: restrict directory to owner read/write/execute only
SECRETS_DIR.chmod(stat.S_IRWXU)

SECRETS_FILE = SECRETS_DIR / "auth.json"


def _secure_write(path: Path, data: str) -> None:
    """Write *data* to *path* with owner-only (0600) permissions, atomically."""
    tmp = path.with_suffix(".tmp")
    # Open with O_CREAT | O_WRONLY | O_TRUNC and mode 0600 from the start
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, stat.S_IRUSR | stat.S_IWUSR)
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write(data)
    except Exception:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise
    tmp.replace(path)
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)


class SecretsService:
    """Service for loading and storing local authentication secrets."""

    @staticmethod
    def load_secrets() -> dict:
        """Return the secrets dict, or an empty dict if no file exists yet."""
        if not SECRETS_FILE.exists():
            return {}
        return json.loads(SECRETS_FILE.read_text())

    @staticmethod
    def save_secret(key: str, value: str) -> None:
        """Persist *key*/*value* into the secrets file with 0600 permissions."""
        secrets = SecretsService.load_secrets()
        secrets[key] = value
        _secure_write(SECRETS_FILE, json.dumps(secrets, indent=2))
