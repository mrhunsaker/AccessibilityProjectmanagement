from db.database import SessionLocal
from models.inventory import InventoryItem, InventoryTransaction

class InventoryService:

    @staticmethod
    def add_inventory(item_id: int, quantity: float, notes: str = ''):
        db = SessionLocal()
        item = db.query(InventoryItem).get(item_id)

        previous = item.current_quantity
        item.current_quantity += quantity

        transaction = InventoryTransaction(
            item_id=item.id,
            transaction_type='ADD',
            quantity=quantity,
            previous_quantity=previous,
            new_quantity=item.current_quantity,
            notes=notes,
        )

        db.add(transaction)
        db.commit()
        db.close()

    @staticmethod
    def consume_inventory(item_id: int, quantity: float, notes: str = '', project_id=None):
        db = SessionLocal()
        item = db.query(InventoryItem).get(item_id)

        previous = item.current_quantity

        if quantity > previous:
            raise ValueError('Insufficient inventory')

        item.current_quantity -= quantity

        transaction = InventoryTransaction(
            item_id=item.id,
            transaction_type='REMOVE',
            quantity=quantity,
            previous_quantity=previous,
            new_quantity=item.current_quantity,
            notes=notes,
            project_id=project_id,
        )

        db.add(transaction)
        db.commit()
        db.close()
