"""결제 클라이언트 재시도 동작 테스트."""

import pytest

from app.payment import PaymentClient, PaymentError


def test_charge_returns_charge_id(payment_stub):
    """정상 응답이면 결제 ID 를 돌려주고 금액과 멱등 키를 보낸다."""
    client = PaymentClient(payment_stub.url)

    assert client.charge("key-1", 15000) == "ch_1"
    assert payment_stub.requests == [
        {"path": "/v1/charges", "idempotency_key": "key-1", "body": {"amount": 15000, "currency": "KRW"}}
    ]


def test_charge_retries_post_when_busy(payment_stub):
    """결제 API 가 503 을 주면 POST 도 재시도해서 성공한다."""
    payment_stub.responses = [503, 503, 200]
    client = PaymentClient(payment_stub.url)

    assert client.charge("key-2", 1000) == "ch_3"
    assert len(payment_stub.requests) == 3
    assert {r["idempotency_key"] for r in payment_stub.requests} == {"key-2"}


def test_charge_gives_up_after_retries(payment_stub):
    """재시도를 다 써도 503 이면 PaymentError 를 낸다."""
    payment_stub.responses = [503] * 10
    client = PaymentClient(payment_stub.url, retries=3)

    with pytest.raises(PaymentError, match="503"):
        client.charge("key-3", 1000)
    assert len(payment_stub.requests) == 4
