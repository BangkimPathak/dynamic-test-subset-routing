import pytest
from src.user_service import UserService


def test_user_register_success():
    svc = UserService()
    user = svc.register("bangkim", "bangkim@example.com", role="engineer")
    assert user["username"] == "bangkim"
    assert user["role"] == "engineer"
    assert user["active"] is True


def test_user_duplicate():
    svc = UserService()
    svc.register("alex", "alex@example.com")
    with pytest.raises(ValueError, match="User already exists"):
        svc.register("alex", "alex2@example.com")


def test_user_invalid_fields():
    svc = UserService()
    with pytest.raises(ValueError, match="at least 3 characters"):
        svc.register("ab", "valid@example.com")
    with pytest.raises(ValueError, match="Invalid email format"):
        svc.register("john", "not-an-email")
