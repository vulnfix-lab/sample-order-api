"""고객 접근 토큰(JWT) 발급과 검증."""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import Settings

ALGORITHM = "HS256"


class InvalidTokenError(Exception):
    """토큰이 위조됐거나 만료됐거나 형식이 틀렸다."""


def issue_token(customer_id: str, settings: Settings, now: datetime | None = None) -> str:
    """고객 ID 를 담은 접근 토큰을 HS256 으로 서명해 발급한다."""
    issued_at = now or datetime.now(timezone.utc)
    claims = {
        "sub": customer_id,
        "iat": int(issued_at.timestamp()),
        "exp": int((issued_at + timedelta(minutes=settings.token_ttl_minutes)).timestamp()),
    }
    return jwt.encode(claims, settings.jwt_secret, algorithm=ALGORITHM)


def verify_token(token: str, settings: Settings) -> str:
    """토큰 서명과 만료를 검증하고 고객 ID 를 돌려준다. 알고리즘은 HS256 으로 고정한다."""
    try:
        claims = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except JWTError as e:
        raise InvalidTokenError(str(e)) from e
    customer_id = claims.get("sub")
    if not customer_id:
        raise InvalidTokenError("sub 클레임이 없습니다")
    return customer_id
