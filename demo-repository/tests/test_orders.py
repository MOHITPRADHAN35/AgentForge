import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from orders import OrderQueue


def test_order_queue_retrieval():
    queue = OrderQueue()
    queue.add_order("ORD-101")
    queue.add_order("ORD-102")
    assert queue.get_order_at(0) == "ORD-101"
    assert queue.get_order_at(1) == "ORD-102"


def test_order_queue_out_of_bounds():
    queue = OrderQueue()
    queue.add_order("ORD-101")
    # This should raise IndexError gracefully, but buggy code raises unhandled index error at boundary
    with pytest.raises(IndexError):
        queue.get_order_at(5)
