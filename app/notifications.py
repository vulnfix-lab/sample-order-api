"""주문 확인 메일 본문 렌더링."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.models import Order

_TEMPLATE_DIR = Path(__file__).parent / "templates"

_env = Environment(
    loader=FileSystemLoader(_TEMPLATE_DIR),
    autoescape=select_autoescape(["html"]),
)
_env.filters["won"] = lambda value: f"{value:,}원"


def render_order_confirmation(order: Order) -> str:
    """주문 확인 메일 HTML 본문을 만든다. 고객이 입력한 값은 자동 이스케이프된다."""
    return _env.get_template("order_confirmation.html").render(order=order)
