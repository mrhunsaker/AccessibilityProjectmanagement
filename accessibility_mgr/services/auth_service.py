"""Authentication helpers for the lightweight UI user switcher."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class UserAccount:
    """Represents a selectable UI user account."""
    username: str
    role: str
    is_admin: bool = False


class AuthService:
    """In-memory user switcher used by the lightweight UI auth flow."""
    users = [
        UserAccount(username="system_admin", role="Administrator", is_admin=True),
        UserAccount(username="operator_user", role="Operator"),
    ]

    current_user = users[0]

    @classmethod
    def list_users(cls):
        """Return all available user accounts."""
        return cls.users

    @classmethod
    def switch_user(cls, username: str):
        """Set and return the active user for a matching username."""
        for user in cls.users:
            if user.username == username:
                cls.current_user = user
                return user

        return None
