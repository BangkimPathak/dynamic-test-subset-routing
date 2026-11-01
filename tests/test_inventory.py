import pytest
from src.inventory import Inventory


def test_inventory_add_and_get():
    inv = Inventory()
    inv.add_stock("laptop", 10)
    assert inv.get_stock("laptop") == 10
    inv.add_stock("laptop", 5)
    assert inv.get_stock("laptop") == 15


def test_inventory_remove():
    inv = Inventory()
    inv.add_stock("mouse", 20)
    inv.remove_stock("mouse", 7)
    assert inv.get_stock("mouse") == 13


def test_inventory_insufficient():
    inv = Inventory()
    inv.add_stock("keyboard", 3)
    with pytest.raises(ValueError, match="not enough stock"):
        inv.remove_stock("keyboard", 5)
