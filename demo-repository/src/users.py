from typing import Optional


class User:
    def __init__(self, username: str, email: Optional[str] = None):
        self.username = username
        self.email = email

    def get_contact_info(self) -> str:
        """
        Bug: Crashes with AttributeError if email is None!
        """
        return user.email.lower()
