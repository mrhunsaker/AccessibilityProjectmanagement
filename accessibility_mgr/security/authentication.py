"""Authentication and API token infrastructure."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(slots=True)
class SessionToken:
    token: str
    username: str
    expires_at: str


@dataclass(slots=True)
class ApiToken:
    name: str
    token: str
    created_at: str


class AuthenticationService:
    """Authentication and token management service."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionToken] = {}
        self._api_tokens: list[ApiToken] = []

    def create_session(self, username: str) -> SessionToken:
        token = secrets.token_hex(24)
        expires = datetime.now(timezone.utc) + timedelta(hours=8)

        session = SessionToken(
            token=token,
            username=username,
            expires_at=expires.isoformat(),
        )

        self._sessions[token] = session
        return session

    def validate_session(self, token: str) -> bool:
        session = self._sessions.get(token)

        if not session:
            return False

        expires = datetime.fromisoformat(session.expires_at)
        return expires > datetime.now(timezone.utc)

    def create_api_token(self, name: str) -> ApiToken:
        token = ApiToken(
            name=name,
            token=secrets.token_hex(32),
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        self._api_tokens.append(token)
        return token

    def list_api_tokens(self) -> list[dict]:
        return [
            {
                "name": token.name,
                "created_at": token.created_at,
            }
            for token in self._api_tokens
        ]


__all__ = [
    "AuthenticationService",
    "SessionToken",
    "ApiToken",
]
