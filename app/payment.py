"""외부 결제 API 클라이언트."""

import json

import urllib3
from urllib3.exceptions import HTTPError
from urllib3.util.retry import Retry

# 결제 API 가 일시적으로 바쁠 때 돌려주는 상태 코드
RETRY_STATUSES = (502, 503, 504)


class PaymentError(Exception):
    """결제 API 호출이 끝내 실패했다."""


class PaymentClient:
    """외부 결제 API 를 urllib3 로 호출한다. 일시 오류는 재시도한다."""

    def __init__(self, base_url: str, retries: int = 3, timeout: float = 3.0) -> None:
        """재시도 정책과 커넥션 풀을 만든다. 결제 API 는 멱등 키를 받으므로 POST 도 재시도한다."""
        retry = Retry(
            total=retries,
            backoff_factor=0.1,
            status_forcelist=RETRY_STATUSES,
            method_whitelist=frozenset({"GET", "POST"}),
            raise_on_status=False,
        )
        self._http = urllib3.PoolManager(retries=retry, timeout=urllib3.Timeout(total=timeout))
        self._base_url = base_url.rstrip("/")

    def charge(self, idempotency_key: str, amount: int) -> str:
        """금액을 결제하고 결제 ID 를 돌려준다. 실패하면 PaymentError 를 낸다."""
        body = json.dumps({"amount": amount, "currency": "KRW"})
        try:
            resp = self._http.request(
                "POST",
                f"{self._base_url}/v1/charges",
                body=body,
                headers={"Content-Type": "application/json", "Idempotency-Key": idempotency_key},
            )
        except HTTPError as e:
            raise PaymentError(f"결제 API 연결 실패: {e}") from e
        if resp.status != 200:
            raise PaymentError(f"결제 API 응답 {resp.status}")
        return json.loads(resp.data)["charge_id"]
