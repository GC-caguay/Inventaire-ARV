from __future__ import annotations

from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))


def render(request: Request, name: str, status_code: int = 200, **context):
    """Wraps Jinja2Templates.TemplateResponse with the modern (request, name, context) signature."""
    return templates.TemplateResponse(request, name, context, status_code=status_code)
