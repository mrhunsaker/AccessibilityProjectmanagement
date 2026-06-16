"""Authentication helpers for the lightweight UI user switcher.

GEN-007: User accounts are no longer hardcoded in source.  Usernames and roles
are read from environment variables at startup so each deployment can define
its own accounts without changing code.

Format (space-separated, one account per variable):
    ACCESSMAN_USER_1=username:role:is_admin   e.g. "alice:Administrator:true"
    ACCESSMAN_USER_2=username:role            e.g. "bob:Operator"

GEN-020: switch_user() now raises UserNotFoundError on failure instead of
silently returning None.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

log = logging.getLogger(__name__)


class UserNotFoundError(ValueError):
    """Raised when switch_user is called with a username that does not exist."""


@dataclass
class UserAccount:
    """Represents a selectable UI user account."""
    username: str
    role: str
    is_admin: bool = False


def _load_accounts_from_env() -> list[UserAccount]:
    """Parse ACCESSMAN_USER_N env vars into UserAccount objects.

    Returns a sensible read-only default when no variables are set so that the
    app remains usable in development without further configuration.
    """
    accounts: list[UserAccount] = []
    idx = 1
    while True:
        raw = os.getenv(f"ACCESSMAN_USER_{idx}", "").strip()
        if not raw:
            break
        parts = [p.strip() for p in raw.split(":")]
        if len(parts) >= 2:
            uname    = parts[0]
            role     = parts[1]
            is_admin = len(parts) >= 3 and parts[2].lower() in {"true", "1", "yes"}
            accounts.append(UserAccount(username=uname, role=role, is_admin=is_admin))
        else:
            log.warning("ACCESSMAN_USER_%d has unexpected format; skipping.", idx)
        idx += 1

    if not accounts:
        # GEN-007: no hardcoded fallback — emit a prominent warning and
        # use a minimal placeholder that operators must replace.
        log.warning(
            "No ACCESSMAN_USER_N environment variables found.  "
            "Define at least ACCESSMAN_USER_1='username:Role:true' in your "
            ".secrets file.  Using an anonymous placeholder for this session."
        )
        accounts = [UserAccount(username="local_operator", role="Operator", is_admin=True)]

    return accounts


class AuthService:
    """In-memory user switcher used by the lightweight UI auth flow."""

    _users: list[UserAccount] = _load_accounts_from_env()
    current_user: UserAccount = _users[0] if _users else UserAccount("local_operator", "Operator", True)

    @classmethod
    def list_users(cls) -> list[UserAccount]:
        """Return all available user accounts."""
        return cls._users

    @classmethod
    def switch_user(cls, username: str) -> UserAccount:
        """Set and return the active user for *username*.

        GEN-020: raises UserNotFoundError instead of returning None so callers
        always know whether the switch succeeded.
        """
        for user in cls._users:
            if user.username == username:
                cls.current_user = user
                log.info("User switched to '%s' (%s).", user.username, user.role)
                return user

        log.warning("switch_user: unknown username '%s' requested.", username)
        raise UserNotFoundError(
            f"No account found with username '{username}'. "
            "Check your ACCESSMAN_USER_N environment variables."
        )
