from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TeamMember
from app.templates_env import render

router = APIRouter(prefix="/members")


@router.get("")
def list_members(request: Request, db: Session = Depends(get_db)):
    members = (
        db.query(TeamMember).order_by(TeamMember.active.desc(), TeamMember.full_name).all()
    )
    return render(request, "members/list.html", members=members)


@router.post("/new")
def create_member(full_name: str = Form(...), db: Session = Depends(get_db)):
    db.add(TeamMember(full_name=full_name.strip()))
    db.commit()
    return RedirectResponse("/members?msg=Membre+ajout%C3%A9", status_code=303)


@router.post("/{member_id}/toggle")
def toggle_member(member_id: int, db: Session = Depends(get_db)):
    member = db.get(TeamMember, member_id)
    if member is None:
        raise HTTPException(404)
    member.active = not member.active
    db.add(member)
    db.commit()
    return RedirectResponse("/members?msg=Mis+%C3%A0+jour", status_code=303)
