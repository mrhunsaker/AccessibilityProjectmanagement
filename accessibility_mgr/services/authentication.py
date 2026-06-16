"""Authentication and API token infrastructure.

GEN-009 / FUN-031: Tokens are currently stored in-memory only and are lost on
restart.  Revocation and token rotation are not persistent.  A future migration
should back this with the database (api_token table).  All validation attempts
are now logged for audit purposes.
"""

from __future__ import annotations

import hashlib
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

log = logging.getLogger(__name__)


@dataclass(slots=True)
class APIToken:
    token_id: str
    token_hash: str
    owner: str
    created_at: str
    expires_at: str
    active: bool


@dataclass(slots=True)
class AuthSession:
    username: str
    session_id: str
    created_at: str
    expires_at: str


class AuthenticationService:
    """Authentication and credential lifecycle service."""

    def __init__(self) -> None:
        self._tokens: list[APIToken] = []
        self._sessions: list[AuthSession] = []

    def create_api_token(
        self,
        *,
        owner: str,
        expiration_hours: int = 24,
    ) -> dict:
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(
            raw_token.encode("utf-8")
        ).hexdigest()

        now = datetime.now(timezone.utc)

        token = APIToken(
            token_id=secrets.token_hex(8),
            token_hash=token_hash,
            owner=owner,
            created_at=now.isoformat(),
            expires_at=(
                now + timedelta(hours=expiration_hours)
            ).isoformat(),
            active=True,
        )

        self._tokens.append(token)

        return {
            "token": raw_token,
            "token_id": token.token_id,
            "expires_at": token.expires_at,
        }

    def register_api_token(
        self,
        *,
        owner: str,
        raw_token: str,
        expiration_hours: int = 24,
    ) -> dict:
        """Register a caller-provided raw API token for validation."""
        token_hash = hashlib.sha256(
            raw_token.encode("utf-8")
        ).hexdigest()
        now = datetime.now(timezone.utc)

        token = APIToken(
            token_id=secrets.token_hex(8),
            token_hash=token_hash,
            owner=owner,
            created_at=now.isoformat(),
            expires_at=(
                now + timedelta(hours=expiration_hours)
            ).isoformat(),
            active=True,
        )

        self._tokens.append(token)
        return {
            "token_id": token.token_id,
            "expires_at": token.expires_at,
        }

    def validate_token(self, raw_token: str, *, caller_ip: str = "unknown") -> bool:
        """Validate *raw_token* and log the attempt.

        FUN-031: every call is logged with timestamp and caller_ip so
        operators can detect brute-force attempts.  Token values are never
        logged — only token_ids.
        """
        hashed = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        now = datetime.now(timezone.utc)

        for token in self._tokens:
            if not token.active:
                continue
            if token.token_hash != hashed:
                continue
            if datetime.fromisoformat(token.expires_at) < now:
                log.warning(
                    "validate_token: expired token presented [id=%s owner=%s ip=%s]",
                    token.token_id, token.owner, caller_ip,
                )
                return False
            log.info(
                "validate_token: accepted [id=%s owner=%s ip=%s]",
                token.token_id, token.owner, caller_ip,
            )
            return True

        log.warning(
            "validate_token: rejected unknown/invalid token [ip=%s at=%s]",
            caller_ip, now.isoformat(),
        )
        return False

    def create_session(
        self,
        *,
        username: str,
        session_hours: int = 8,
    ) -> AuthSession:
        now = datetime.now(timezone.utc)

        session = AuthSession(
            username=username,
            session_id=secrets.token_hex(16),
            created_at=now.isoformat(),
            expires_at=(
                now + timedelta(hours=session_hours)
            ).isoformat(),
        )

        self._sessions.append(session)
        return session

    def list_tokens(self) -> list[dict]:
        return [
            {
                "token_id": token.token_id,
                "owner": token.owner,
                "expires_at": token.expires_at,
                "active": token.active,
            }
            for token in self._tokens
        ]


__all__ = [
    "AuthenticationService",
    "APIToken",
    "AuthSession",
]
