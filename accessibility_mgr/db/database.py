from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = 'sqlite:///accessibility_manager.db'

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

def init_db():
    from models.inventory import Category, InventoryItem, InventoryTransaction
    Base.metadata.create_all(bind=engine)
