from typing import List


class OrderQueue:
    def __init__(self):
        self.orders: List[str] = []

    def add_order(self, order_id: str):
        self.orders.append(order_id)

    def get_order_at(self, index: int) -> str:
        """
        Bug: Boundary check uses '<=' instead of '<', raising IndexError!
        """
        if index <= len(self.orders):
            return self.orders[index]
        raise IndexError("Order index out of range")
