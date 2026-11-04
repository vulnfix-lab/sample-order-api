"""FastAPI 앱 조립과 라우트.

실행: uvicorn app.main:create_app --factory
"""

import uuid

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth import InvalidTokenError, issue_token, verify_token
from app.config import Settings, get_settings
from app.models import Order, OrderCreate, TokenRequest, TokenResponse
from app.notifications import render_order_confirmation
from app.payment import PaymentClient, PaymentError
from app.store import OrderStore

_bearer = HTTPBearer(auto_error=False)


def current_customer(
    request: Request,
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """Authorization 헤더의 토큰을 검증해 고객 ID 를 돌려준다. 없거나 틀리면 401."""
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "토큰이 필요합니다")
    try:
        return verify_token(cred.credentials, request.app.state.settings)
    except InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "유효하지 않은 토큰입니다") from None


def create_app(settings: Settings | None = None, payment_client: PaymentClient | None = None) -> FastAPI:
    """설정과 결제 클라이언트를 붙여 FastAPI 앱을 만든다."""
    settings = settings or get_settings()
    app = FastAPI(title="Sample Order API", version="0.1.0")
    app.state.settings = settings
    app.state.payment = payment_client or PaymentClient(settings.payment_api_base_url)
    app.state.store = OrderStore()
    # 메일 발송은 범위 밖이라 렌더한 본문을 발송 대기함에 쌓기만 한다
    app.state.outbox = []

    @app.get("/health")
    def health() -> dict:
        """헬스 체크."""
        return {"status": "ok"}

    @app.post("/auth/token", response_model=TokenResponse)
    def create_token(body: TokenRequest) -> TokenResponse:
        """데모용 토큰 발급. 실제 고객 인증은 범위 밖이다."""
        return TokenResponse(access_token=issue_token(body.customer_id, settings))

    @app.post("/orders", response_model=Order, status_code=status.HTTP_201_CREATED)
    def create_order(body: OrderCreate, customer_id: str = Depends(current_customer)) -> Order:
        """주문 금액을 결제하고 주문을 저장한 뒤 확인 메일을 대기함에 넣는다."""
        total = sum(item.unit_price * item.quantity for item in body.items)
        try:
            payment_id = app.state.payment.charge(uuid.uuid4().hex, total)
        except PaymentError as e:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"결제 실패: {e}") from None
        order = app.state.store.add(customer_id, body, total, payment_id)
        app.state.outbox.append({"to": order.customer_email, "html": render_order_confirmation(order)})
        return order

    @app.get("/orders/{order_id}", response_model=Order)
    def get_order(order_id: int, customer_id: str = Depends(current_customer)) -> Order:
        """본인 주문만 조회한다. 남의 주문은 없는 주문처럼 404 로 응답한다."""
        order = app.state.store.get(order_id)
        if order is None or order.customer_id != customer_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "주문이 없습니다")
        return order

    return app
