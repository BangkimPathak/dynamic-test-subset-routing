class Inventory:
    """Stock tracking and warehouse inventory management."""
    def __init__(self):
        self.stock = {}

    def add_stock(self, item: str, qty: int):
        if qty <= 0:
            raise ValueError("Quantity must be positive")
        self.stock[item] = self.stock.get(item, 0) + qty

    def remove_stock(self, item: str, qty: int):
        if qty <= 0:
            raise ValueError("Quantity must be positive")
        if self.stock.get(item, 0) < qty:
            raise ValueError("not enough stock")
        self.stock[item] -= qty

    def get_stock(self, item: str) -> int:
        return self.stock.get(item, 0)
