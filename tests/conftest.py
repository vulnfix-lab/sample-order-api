"""테스트 공통 픽스처: 결제 API stub 서버, 설정, 테스트 클라이언트."""

import json
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


class PaymentStub:
    """로컬에서 뜨는 가짜 결제 API. 미리 넣어 둔 상태 코드 순서대로 응답한다."""

    def __init__(self) -> None:
        self.responses: list[int] = []
        self.requests: list[dict] = []
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length", 0))
                stub.requests.append({
                    "path": self.path,
                    "idempotency_key": self.headers.get("Idempotency-Key"),
                    "body": json.loads(self.rfile.read(length) or b"{}"),
                })
                code = stub.responses.pop(0) if stub.responses else 200
                payload = {"charge_id": f"ch_{len(stub.requests)}"} if code == 200 else {"error": "busy"}
                data = json.dumps(payload).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args) -> None:
                pass

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self._server.server_address[1]}"
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def close(self) -> None:
        """stub 서버를 내린다."""
        self._server.shutdown()
        self._server.server_close()


@pytest.fixture
def payment_stub():
    """테스트마다 새 결제 stub 서버를 띄운다."""
    stub = PaymentStub()
    yield stub
    stub.close()


@pytest.fixture
def settings(monkeypatch, payment_stub):
    """테스트용 비밀 값을 실행 시 만들어 환경변수로 넣고 설정을 읽는다."""
    monkeypatch.setenv("ORDER_API_JWT_SECRET", secrets.token_hex(32))
    monkeypatch.setenv("PAYMENT_API_BASE_URL", payment_stub.url)
    return get_settings()


@pytest.fixture
def client(settings):
    """실제 결제 클라이언트(urllib3)를 붙인 앱의 테스트 클라이언트."""
    with TestClient(create_app(settings)) as c:
        yield c


@pytest.fixture
def auth_headers(client):
    """고객 c-100 의 토큰 헤더를 만든다."""
    token = client.post("/auth/token", json={"customer_id": "c-100"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
