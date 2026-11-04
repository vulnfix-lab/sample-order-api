"""환경변수에서 앱 설정을 읽는다."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """앱 설정 값 묶음."""

    jwt_secret: str
    payment_api_base_url: str
    token_ttl_minutes: int = 30


def _require(name: str) -> str:
    """필수 환경변수를 읽는다. 없으면 바로 실패한다."""
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"환경변수 {name} 가 필요합니다")
    return value


def get_settings() -> Settings:
    """환경변수에서 설정을 읽어 Settings 로 돌려준다. 비밀 값의 기본값은 두지 않는다."""
    return Settings(
        jwt_secret=_require("ORDER_API_JWT_SECRET"),
        payment_api_base_url=_require("PAYMENT_API_BASE_URL").rstrip("/"),
        token_ttl_minutes=int(os.environ.get("ORDER_API_TOKEN_TTL_MINUTES", "30")),
    )
