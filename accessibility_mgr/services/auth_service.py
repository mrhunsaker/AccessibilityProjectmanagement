"""Authentication helpers for the lightweight UI user switcher."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class UserAccount:
    """UserAccount class.
    
    """
    username: str
    role: str
    is_admin: bool = False


class AuthService:
    """AuthService class.
    
    """
    users = [
        UserAccount(username="system_admin", role="Administrator", is_admin=True),
        UserAccount(username="operator_user", role="Operator"),
    ]

    current_user = users[0]

    @classmethod
    def list_users(cls):
        """List users.
        
        Returns
        -------
        Any
            Function result.
        
        """
        return cls.users

    @classmethod
    def switch_user(cls, username: str):
        """Switch user.
        
        Parameters
        ----------
        username : Any
            username parameter.
        
        Returns
        -------
        Any
            Function result.
        
        """
        for user in cls.users:
            if user.username == username:
                cls.current_user = user
                return user

        return None
