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
        # FUN-024: validate inputs before attempting encryption
        if not name or not name.strip():
            raise ValueError("Secret name must be a non-empty string.")
        if value is None:
            raise ValueError("Secret value must not be None.")

        record = SecretRecord(
            name=name.strip(),
            encrypted_value=self._encrypt(value),
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        self._secrets[name.strip()] = record
        return record

    def retrieve_secret(self, name: str) -> str | None:
        # FUN-024: validate lookup key
        if not name or not name.strip():
            raise ValueError("Secret name must be a non-empty string.")

        record = self._secrets.get(name.strip())
        if not record:
            return None

        # FUN-025: surface decryption failures with a useful message
        try:
            return self._decrypt(record.encrypted_value)
        except ValueError as exc:
            raise RuntimeError(
                f"Secret '{name}' exists but could not be decrypted. "
                "The vault key may have changed since the secret was stored."
            ) from exc

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
