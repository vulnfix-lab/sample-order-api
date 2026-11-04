"""접근 토큰 발급·검증 테스트."""

import secrets
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from app.auth import InvalidTokenError, issue_token, verify_token


def test_issue_and_verify_roundtrip(settings):
    """발급한 토큰을 검증하면 고객 ID 가 나온다."""
    token = issue_token("c-100", settings)

    assert verify_token(token, settings) == "c-100"


def test_token_signed_with_other_secret_is_rejected(settings):
    """다른 비밀 값으로 서명한 토큰은 거부한다."""
    forged = issue_token("c-100", replace(settings, jwt_secret=secrets.token_hex(32)))

    with pytest.raises(InvalidTokenError):
        verify_token(forged, settings)


def test_expired_token_is_rejected(settings):
    """만료된 토큰은 거부한다."""
    past = datetime.now(timezone.utc) - timedelta(minutes=settings.token_ttl_minutes + 5)
    token = issue_token("c-100", settings, now=past)

    with pytest.raises(InvalidTokenError):
        verify_token(token, settings)
