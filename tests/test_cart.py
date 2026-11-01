import pytest
from src.cart import Cart


def test_cart_empty():
    c = Cart()
    assert c.subtotal() == 0
    assert c.total() == 0


def test_cart_add_and_total():
    c = Cart()
    c.add("Book", 50, 2)
    c.add("Pen", 10, 5)
    assert c.subtotal() == 150.0
    # subtotal 150 with 10% discount -> 135 -> with 18% tax -> 159.30
    assert c.total(discount=10) == 159.30


def test_cart_invalid_items():
    c = Cart()
    with pytest.raises(ValueError):
        c.add("BadItem", -10, 1)
    with pytest.raises(ValueError):
        c.add("BadQty", 10, 0)
