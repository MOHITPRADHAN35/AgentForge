import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from users import User


def test_user_contact_with_email():
    user = User("alice", "ALICE@EXAMPLE.COM")
    assert user.get_contact_info() == "alice@example.com"


def test_user_contact_none_email():
    user = User("bob", None)
    # This will fail on broken code
    assert user.get_contact_info() == ""
