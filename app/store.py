"""주문을 메모리에 보관하는 저장소."""

import threading

from app.models import Order, OrderCreate


class OrderStore:
    """프로세스 메모리에 주문을 보관한다. 재시작하면 사라진다."""

    def __init__(self) -> None:
        self._orders: dict[int, Order] = {}
        self._next_id = 1
        self._lock = threading.Lock()

    def add(self, customer_id: str, data: OrderCreate, total: int, payment_id: str) -> Order:
        """결제가 끝난 주문을 새 ID 로 저장하고 돌려준다."""
        with self._lock:
            order = Order(
                id=self._next_id,
                customer_id=customer_id,
                customer_name=data.customer_name,
                customer_email=data.customer_email,
                items=data.items,
                total=total,
                payment_id=payment_id,
            )
            self._orders[order.id] = order
            self._next_id += 1
            return order

    def get(self, order_id: int) -> Order | None:
        """주문 ID 로 주문을 찾는다. 없으면 None."""
        return self._orders.get(order_id)

    def count(self) -> int:
        """저장된 주문 수를 돌려준다."""
        return len(self._orders)
