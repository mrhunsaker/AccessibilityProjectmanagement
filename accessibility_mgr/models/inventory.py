"""Legacy SQLAlchemy inventory compatibility models.

The modern application architecture primarily uses the SQLite query helpers in
``accessibility_mgr.db.queries``. These ORM models are retained for backward
compatibility with older admin tooling, migration utilities, and historical
documentation examples referenced in the docs directory.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.database import Base


class Category(Base):
    """Inventory category definition."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, default="")


class InventoryItem(Base):
    """Tracked inventory item."""

    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(128), nullable=True)
    current_quantity: Mapped[float] = mapped_column(Float, default=0)
    unit: Mapped[str] = mapped_column(String(32), default="pcs")
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    category_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("categories.id"),
        nullable=True,
    )

    category: Mapped[Category | None] = relationship()


class InventoryTransaction(Base):
    """Audit history for inventory quantity changes."""

    __tablename__ = "inventory_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("inventory_items.id"),
        nullable=False,
    )
    transaction_type: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity_delta: Mapped[float] = mapped_column(Float, nullable=False)
    previous_quantity: Mapped[float] = mapped_column(Float, nullable=False)
    new_quantity: Mapped[float] = mapped_column(Float, nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    item: Mapped[InventoryItem] = relationship()


__all__ = [
    "Category",
    "InventoryItem",
    "InventoryTransaction",
]
