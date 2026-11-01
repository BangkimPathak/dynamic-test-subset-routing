import pytest
from src.test_router import DynamicTestRouter


@pytest.fixture
def router():
    return DynamicTestRouter()


def test_docs_change_skips_all_tests(router):
    """When only documentation or asset files change, all tests must be skipped."""
    changed = ["README.md", "docs/architecture.png", "notes.txt"]
    decision = router.route_tests(changed)
    assert decision["strategy"] == "SKIP_ALL"
    assert len(decision["selected_tests"]) == 0


def test_global_config_triggers_full_regression(router):
    """Modifying requirements.txt or pytest.ini must trigger a full regression suite."""
    changed = ["requirements.txt"]
    decision = router.route_tests(changed)
    assert decision["strategy"] == "FULL_REGRESSION"
    assert len(decision["selected_tests"]) >= 5


def test_isolated_module_routing(router):
    """
    Modifying src/inventory.py should only route tests/test_inventory.py,
    sparing all other unrelated test suites.
    """
    changed = ["src/inventory.py"]
    decision = router.route_tests(changed)
    assert decision["strategy"] == "TARGETED_SUBSET"
    assert "tests/test_inventory.py" in decision["selected_tests"]
    assert "tests/test_pricing.py" not in decision["selected_tests"]
    assert "tests/test_user_service.py" not in decision["selected_tests"]


def test_transitive_dependency_routing(router):
    """
    Modifying src/pricing.py must transitively route:
      - tests/test_pricing.py (direct)
      - tests/test_cart.py (cart imports pricing)
      - tests/test_payment_gateway.py (payment imports pricing)
    while completely excluding test_inventory.py and test_user_service.py.
    """
    changed = ["src/pricing.py"]
    decision = router.route_tests(changed)
    assert decision["strategy"] == "TARGETED_SUBSET"
    selected = decision["selected_tests"]

    assert "tests/test_pricing.py" in selected
    assert "tests/test_cart.py" in selected
    assert "tests/test_payment_gateway.py" in selected
    assert "tests/test_inventory.py" not in selected


def test_direct_test_file_routing(router):
    """Editing a test file directly routes only that test file."""
    changed = ["tests/test_cart.py"]
    decision = router.route_tests(changed)
    assert decision["strategy"] == "TARGETED_SUBSET"
    assert decision["selected_tests"] == ["tests/test_cart.py"]


def test_dynamic_sharding(router):
    """Partitions 6 tests across 3 shards evenly (2 tests per shard)."""
    tests = [
        "tests/test_1.py", "tests/test_2.py", "tests/test_3.py",
        "tests/test_4.py", "tests/test_5.py", "tests/test_6.py"
    ]
    shards = router.shard_tests(tests, num_shards=3)
    assert len(shards) == 3
    assert len(shards[1]) == 2
    assert len(shards[2]) == 2
    assert len(shards[3]) == 2
