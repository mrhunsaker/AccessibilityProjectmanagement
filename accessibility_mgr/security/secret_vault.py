"""Encrypted credential and secret vault infrastructure."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(slots=True)
class SecretRecord:
    name: str
    encrypted_value: str
    created_at: str


class SecretVaultService:
    """Credential and secret vault service."""

    def __init__(self) -> None:
        try:
            from cryptography.fernet import Fernet
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "cryptography is required for SecretVaultService encryption"
            ) from exc

        key = os.getenv("ACCESSMAN_VAULT_KEY", "").strip()
        if not key:
            raise RuntimeError(
                "ACCESSMAN_VAULT_KEY is required. "
                "Set a Fernet key before starting the application."
            )

        try:
            self._fernet = Fernet(key.encode("utf-8"))
        except (ValueError, TypeError) as exc:
            raise RuntimeError(
                "ACCESSMAN_VAULT_KEY is invalid. "
                "Generate one with cryptography.fernet.Fernet.generate_key()."
            ) from exc

        self._secrets: dict[str, SecretRecord] = {}

    def _encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def _decrypt(self, value: str) -> str:
        try:
            return self._fernet.decrypt(value.encode("utf-8")).decode("utf-8")
        except Exception:
            raise ValueError("Secret could not be decrypted with the configured vault key")

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
