"""주문 API 테스트. 결제는 로컬 stub 서버를 실제 urllib3 클라이언트로 호출한다."""

ORDER = {
    "customer_name": "홍길동",
    "customer_email": "hong@example.com",
    "items": [
        {"sku": "BOOK-01", "quantity": 2, "unit_price": 12000},
        {"sku": "PEN-07", "quantity": 1, "unit_price": 3000},
    ],
}


def test_create_order_charges_and_queues_mail(client, auth_headers, payment_stub):
    """주문하면 합계를 결제하고 확인 메일을 대기함에 넣는다."""
    resp = client.post("/orders", json=ORDER, headers=auth_headers)

    assert resp.status_code == 201
    body = resp.json()
    assert body["total"] == 27000
    assert body["customer_id"] == "c-100"
    assert body["payment_id"] == "ch_1"
    assert payment_stub.requests[0]["body"]["amount"] == 27000
    outbox = client.app.state.outbox
    assert len(outbox) == 1
    assert outbox[0]["to"] == "hong@example.com"
    assert "27,000원" in outbox[0]["html"]


def test_create_order_retries_when_payment_busy(client, auth_headers, payment_stub):
    """결제 API 가 잠깐 바빠도 재시도로 주문이 성공한다."""
    payment_stub.responses = [503, 200]

    resp = client.post("/orders", json=ORDER, headers=auth_headers)

    assert resp.status_code == 201
    assert len(payment_stub.requests) == 2


def test_payment_failure_returns_502(client, auth_headers, payment_stub):
    """결제가 끝내 실패하면 502 를 주고 주문을 저장하지 않는다."""
    payment_stub.responses = [503] * 10

    resp = client.post("/orders", json=ORDER, headers=auth_headers)

    assert resp.status_code == 502
    assert client.app.state.store.count() == 0
    assert client.app.state.outbox == []


def test_get_order_only_for_owner(client, auth_headers):
    """본인 주문은 조회되고 남의 주문은 404 다."""
    order_id = client.post("/orders", json=ORDER, headers=auth_headers).json()["id"]
    other = client.post("/auth/token", json={"customer_id": "c-200"}).json()["access_token"]

    assert client.get(f"/orders/{order_id}", headers=auth_headers).status_code == 200
    assert client.get(f"/orders/{order_id}", headers={"Authorization": f"Bearer {other}"}).status_code == 404


def test_order_requires_valid_token(client):
    """토큰이 없거나 틀리면 401 이다."""
    assert client.post("/orders", json=ORDER).status_code == 401
    assert client.post("/orders", json=ORDER, headers={"Authorization": "Bearer not-a-jwt"}).status_code == 401


def test_invalid_order_body_returns_422(client, auth_headers):
    """수량이 0 이거나 항목이 비면 422 다."""
    bad_qty = {**ORDER, "items": [{"sku": "BOOK-01", "quantity": 0, "unit_price": 12000}]}
    no_items = {**ORDER, "items": []}

    assert client.post("/orders", json=bad_qty, headers=auth_headers).status_code == 422
    assert client.post("/orders", json=no_items, headers=auth_headers).status_code == 422
