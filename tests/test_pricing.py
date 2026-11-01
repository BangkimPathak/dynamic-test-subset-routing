import pytest
from src.pricing import apply_discount, add_tax


def test_discount_basic():
    assert apply_discount(100, 10) == 90.0
    assert apply_discount(250, 20) == 200.0


def test_discount_boundaries():
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(100, 100) == 0.0


def test_discount_invalid():
    with pytest.raises(ValueError):
        apply_discount(100, 105)
    with pytest.raises(ValueError):
        apply_discount(100, -5)


def test_tax_calculation():
    assert add_tax(100) == 118.0
    assert add_tax(100, rate=0.05) == 105.0
