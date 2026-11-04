# sample-order-api

오픈소스 취약점 조치 Agent 를 평가하려고 만든 **테스트 대상 저장소**입니다.
작은 FastAPI 주문 API 이고, 취약점이 알려진 실제 패키지의 과거 버전을 일부러 고정해 두었습니다.

> **주의: 취약한 의존성을 일부러 쓰는 앱입니다.** 외부에 띄우지 말고 로컬 테스트로만 씁니다.
> Dependabot security updates 는 꺼 둡니다(평가용 상태를 유지하기 위해).

## 구성

| 경로 | 역할 |
|---|---|
| `app/main.py` | 앱 조립과 라우트 (`/health`, `/auth/token`, `/orders`) |
| `app/auth.py` | 접근 토큰 발급·검증 (python-jose, HS256) |
| `app/payment.py` | 외부 결제 API 클라이언트 (urllib3, 재시도) |
| `app/notifications.py` | 주문 확인 메일 렌더 (jinja2) |
| `app/config.py` | 환경변수 설정 |
| `tests/` | pytest 테스트, 결제 API stub 서버 |
| `tests/seed_orders.py` | 로컬 서버 시드 스크립트 (개발 전용, requests) |

## 의존성 파일

- `requirements.in` → `requirements.txt`: 운영 의존성 (pip-tools lock)
- `requirements-dev.in` → `requirements-dev.txt`: 개발·테스트 전용 의존성

lock 다시 만들기:

```bash
pip install pip-tools
pip-compile --strip-extras --output-file=requirements.txt requirements.in
pip-compile --strip-extras --output-file=requirements-dev.txt requirements-dev.in
```

## 설치와 테스트

Python 3.14 에서 확인했습니다.

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt -r requirements-dev.txt
.venv/Scripts/python -m pytest
```

## 로컬 실행

비밀 값은 환경변수로만 받습니다. 코드와 저장소에 넣지 않습니다.

```bash
export ORDER_API_JWT_SECRET=<임의의 긴 값>
export PAYMENT_API_BASE_URL=http://127.0.0.1:9000
.venv/Scripts/python -m uvicorn app.main:create_app --factory --host 127.0.0.1
```
