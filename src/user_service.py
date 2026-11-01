import re
from typing import Dict, Optional


class UserService:
    """User account validation and session management."""
    def __init__(self):
        self.users: Dict[str, dict] = {}

    def register(self, username: str, email: str, role: str = "customer") -> dict:
        if not username or len(username) < 3:
            raise ValueError("Username must be at least 3 characters")
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Invalid email format")
        if username in self.users:
            raise ValueError("User already exists")

        user_data = {"username": username, "email": email, "role": role, "active": True}
        self.users[username] = user_data
        return user_data

    def get_user(self, username: str) -> Optional[dict]:
        return self.users.get(username)
