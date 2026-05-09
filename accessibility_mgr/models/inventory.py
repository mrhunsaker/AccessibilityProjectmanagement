from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from db.database import Base

class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)

    items = relationship('InventoryItem', back_populates='category')

class InventoryItem(Base):
    __tablename__ = 'inventory_items'

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.id'))
    name = Column(String, nullable=False)
    description = Column(Text)
    sku = Column(String)
    unit = Column(String, default='units')
    current_quantity = Column(Float, default=0)
    minimum_quantity = Column(Float, default=0)

    category = relationship('Category', back_populates='items')
    transactions = relationship('InventoryTransaction', back_populates='item')

class InventoryTransaction(Base):
    __tablename__ = 'inventory_transactions'

    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('inventory_items.id'))
    transaction_type = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    previous_quantity = Column(Float, nullable=False)
    new_quantity = Column(Float, nullable=False)
    notes = Column(Text)
    project_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    item = relationship('InventoryItem', back_populates='transactions')
