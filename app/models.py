"""주문 API 의 요청·응답 모델."""

from typing import Literal

from pydantic import BaseModel, Field


class OrderItem(BaseModel):
    """주문 항목 하나."""

    sku: str = Field(min_length=1, max_length=32)
    quantity: int = Field(gt=0, le=100)
    unit_price: int = Field(gt=0, description="원 단위 단가")


class OrderCreate(BaseModel):
    """주문 생성 요청."""

    customer_name: str = Field(min_length=1, max_length=50)
    customer_email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    items: list[OrderItem] = Field(min_length=1, max_length=20)


class Order(BaseModel):
    """결제까지 끝난 주문."""

    id: int
    customer_id: str
    customer_name: str
    customer_email: str
    items: list[OrderItem]
    total: int
    status: Literal["paid"] = "paid"
    payment_id: str


class TokenRequest(BaseModel):
    """토큰 발급 요청. 데모용이라 고객 ID 만 받는다."""

    customer_id: str = Field(min_length=1, max_length=32)


class TokenResponse(BaseModel):
    """토큰 발급 응답."""

    access_token: str
    token_type: Literal["bearer"] = "bearer"
