import pytest
import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from payments import PaymentProcessor


def test_payment_tax():
    processor = PaymentProcessor()
    assert processor.apply_tax(100.0, 0.1) == 110.0


def test_payment_tax_zero():
    processor = PaymentProcessor()
    assert processor.apply_tax(50.0, 0.0) == 50.0


def test_calculate_discount_normal():
    processor = PaymentProcessor()
    assert processor.calculate_discount(100.0, 5) == 20.0


def test_calculate_discount_zero_items():
    processor = PaymentProcessor()
    # This will fail on broken code with ZeroDivisionError
    assert processor.calculate_discount(100.0, 0) == 0.0
