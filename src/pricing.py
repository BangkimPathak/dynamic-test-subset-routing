def apply_discount(price: float, percent: float) -> float:
    """Applies a percentage discount to price rounded to 2 decimals."""
    if not 0 <= percent <= 100:
        raise ValueError("percent must be between 0 and 100")
    return round(price * (1 - percent / 100), 2)


def add_tax(price: float, rate: float = 0.18) -> float:
    """Adds tax to price (default 18% GST)."""
    return round(price * (1 + rate), 2)
