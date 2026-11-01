import uuid
from src.user_service import UserService
from src.pricing import add_tax


class PaymentGateway:
    """Payment transaction processor with user identity verification."""
    def __init__(self, user_service: UserService = None):
        self.user_service = user_service or UserService()
        self.transactions = []

    def process_payment(self, username: str, amount: float) -> dict:
        user = self.user_service.get_user(username)
        if not user or not user.get("active"):
            raise ValueError("Invalid or inactive user")
        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero")

        total_charged = add_tax(amount, rate=0.02)  # 2% processing fee
        txn = {
            "txn_id": str(uuid.uuid4())[:8],
            "username": username,
            "base_amount": amount,
            "total_charged": total_charged,
            "status": "COMPLETED"
        }
        self.transactions.append(txn)
        return txn
