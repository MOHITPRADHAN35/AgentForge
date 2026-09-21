class PaymentProcessor:
    def __init__(self, currency: str = "USD"):
        self.currency = currency

    def calculate_discount(self, total: float, quantity: int) -> float:
        """
        Calculates per-item discount based on order size.
        Bug: Division by zero when quantity is 0!
        """
        return total / quantity

    def apply_tax(self, amount: float, tax_rate: float) -> float:
        if amount < 0 or tax_rate < 0:
            raise ValueError("Amount and tax rate must be non-negative")
        return round(amount * (1 + tax_rate), 2)
