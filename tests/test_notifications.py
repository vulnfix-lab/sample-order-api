"""주문 확인 메일 렌더링 테스트."""

from app.models import Order, OrderItem
from app.notifications import render_order_confirmation


def _order(name: str) -> Order:
    """테스트용 주문을 만든다."""
    return Order(
        id=7,
        customer_id="c-100",
        customer_name=name,
        customer_email="hong@example.com",
        items=[OrderItem(sku="BOOK-01", quantity=2, unit_price=12000)],
        total=24000,
        payment_id="ch_1",
    )


def test_confirmation_lists_items_and_total():
    """메일 본문에 주문 번호, 상품, 합계가 들어간다."""
    html = render_order_confirmation(_order("홍길동"))

    assert "홍길동 님" in html
    assert "주문 번호: 7" in html
    assert "BOOK-01" in html
    assert "합계: 24,000원" in html


def test_customer_input_is_escaped():
    """고객이 입력한 이름의 HTML 은 이스케이프된다."""
    html = render_order_confirmation(_order("<script>alert(1)</script>"))

    assert "<script>" not in html
    assert "&lt;script&gt;" in html
