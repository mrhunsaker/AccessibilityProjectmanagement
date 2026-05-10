from __future__ import annotations

import json
from pathlib import Path


SECRETS_DIR = Path("secrets")
SECRETS_DIR.mkdir(exist_ok=True)

SECRETS_FILE = SECRETS_DIR / "auth.json"


class SecretsService:
    @staticmethod
    def load_secrets() -> dict:
        if not SECRETS_FILE.exists():
            return {}

        return json.loads(SECRETS_FILE.read_text())

    @staticmethod
    def save_secret(key: str, value: str):
        secrets = SecretsService.load_secrets()
        secrets[key] = value
        SECRETS_FILE.write_text(json.dumps(secrets, indent=2))
