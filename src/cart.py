from src.pricing import apply_discount, add_tax


class Cart:
    """Shopping cart abstraction with items and price calculations."""
    def __init__(self):
        self.items = []

    def add(self, name: str, price: float, qty: int = 1):
        if price < 0 or qty <= 0:
            raise ValueError("Price and quantity must be positive")
        self.items.append((name, price, qty))

    def subtotal(self) -> float:
        return sum(p * q for _, p, q in self.items)

    def total(self, discount: float = 0) -> float:
        st = self.subtotal()
        return add_tax(apply_discount(st, discount))
