"""Encrypted credential and secret vault infrastructure."""

from __future__ import annotations

import base64
from dataclasses import dataclass, asdict
from datetime import datetime, timezone


@dataclass(slots=True)
class SecretRecord:
    name: str
    encrypted_value: str
    created_at: str


class SecretVaultService:
    """Credential and secret vault service."""

    def __init__(self) -> None:
        self._secrets: dict[str, SecretRecord] = {}

    def _encrypt(self, value: str) -> str:
        return base64.b64encode(value.encode("utf-8")).decode("utf-8")

    def _decrypt(self, value: str) -> str:
        return base64.b64decode(value.encode("utf-8")).decode("utf-8")

    def store_secret(
        self,
        *,
        name: str,
        value: str,
    ) -> SecretRecord:
        record = SecretRecord(
            name=name,
            encrypted_value=self._encrypt(value),
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        self._secrets[name] = record
        return record

    def retrieve_secret(self, name: str) -> str | None:
        record = self._secrets.get(name)

        if not record:
            return None

        return self._decrypt(record.encrypted_value)

    def list_secrets(self) -> list[dict]:
        return [
            {
                "name": secret.name,
                "created_at": secret.created_at,
            }
            for secret in self._secrets.values()
        ]


__all__ = [
    "SecretVaultService",
    "SecretRecord",
]
