from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///accessibility_manager.db"

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


def init_db():
    from ..models.assets import (
        Asset,
        AssetMetadata,
        Project,
        WorkflowEvent,
    )
    from ..models.inventory import Category, InventoryItem, InventoryTransaction

    Base.metadata.create_all(bind=engine)
