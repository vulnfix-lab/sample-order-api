"""로컬 개발 서버에 시드 주문을 넣는 수동 스크립트. 개발 전용이며 운영 코드와 테스트에서 쓰지 않는다.

사용: python tests/seed_orders.py --base-url http://127.0.0.1:8000 --count 5
"""

import argparse

import requests

SAMPLE_ITEMS = [
    {"sku": "BOOK-01", "quantity": 1, "unit_price": 12000},
    {"sku": "PEN-07", "quantity": 3, "unit_price": 3000},
]


def seed(base_url: str, customer_id: str, count: int) -> list[int]:
    """토큰을 발급받아 시드 주문을 count 건 만들고 주문 ID 목록을 돌려준다."""
    with requests.Session() as session:
        resp = session.post(f"{base_url}/auth/token", json={"customer_id": customer_id}, timeout=5)
        resp.raise_for_status()
        session.headers["Authorization"] = f"Bearer {resp.json()['access_token']}"
        order_ids = []
        for n in range(count):
            body = {
                "customer_name": f"시드고객{n + 1}",
                "customer_email": f"seed{n + 1}@example.com",
                "items": SAMPLE_ITEMS,
            }
            resp = session.post(f"{base_url}/orders", json=body, timeout=10)
            resp.raise_for_status()
            order_ids.append(resp.json()["id"])
        return order_ids


def main() -> None:
    """명령행 인자를 읽어 시드 주문을 만든다."""
    parser = argparse.ArgumentParser(description="로컬 서버에 시드 주문을 넣는다")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--customer-id", default="seed-customer")
    parser.add_argument("--count", type=int, default=3)
    args = parser.parse_args()
    print(seed(args.base_url.rstrip("/"), args.customer_id, args.count))


if __name__ == "__main__":
    main()
