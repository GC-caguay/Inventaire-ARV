from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.dashboard_service import get_active_loans, get_dashboard_stats
from app.templates_env import render

router = APIRouter()


@router.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
    stats = get_dashboard_stats(db)
    active_loans = get_active_loans(db)
    return render(request, "dashboard.html", stats=stats, active_loans=active_loans)
