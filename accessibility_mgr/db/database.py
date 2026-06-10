"""Legacy SQLAlchemy compatibility base.

The primary application uses direct SQLite helpers from db.queries, but
legacy ORM models import Base from this module.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for compatibility ORM models."""


__all__ = [
    "Base",
]
