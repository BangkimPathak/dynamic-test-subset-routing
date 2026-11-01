import pytest
from src.user_service import UserService
from src.payment_gateway import PaymentGateway


def test_payment_success():
    users = UserService()
    users.register("alice", "alice@example.com")
    gw = PaymentGateway(user_service=users)

    txn = gw.process_payment("alice", 200.0)
    assert txn["status"] == "COMPLETED"
    assert txn["base_amount"] == 200.0
    # 200 + 2% fee = 204.0
    assert txn["total_charged"] == 204.0
    assert len(gw.transactions) == 1


def test_payment_unknown_user():
    gw = PaymentGateway()
    with pytest.raises(ValueError, match="Invalid or inactive user"):
        gw.process_payment("ghost", 100.0)


def test_payment_invalid_amount():
    users = UserService()
    users.register("bob", "bob@example.com")
    gw = PaymentGateway(user_service=users)
    with pytest.raises(ValueError, match="greater than zero"):
        gw.process_payment("bob", -50.0)
