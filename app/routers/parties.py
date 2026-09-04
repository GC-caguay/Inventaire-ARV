from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Party
from app.templates_env import templates

router = APIRouter(prefix="/parties")


@router.get("")
def list_parties(request: Request, db: Session = Depends(get_db)):
    parties = db.query(Party).order_by(Party.active.desc(), Party.name).all()
    return templates.TemplateResponse("parties/list.html", {"request": request, "parties": parties})


@router.post("/new")
def create_party(
    name: str = Form(...),
    party_type: str = Form(""),
    contact_info: str = Form(""),
    db: Session = Depends(get_db),
):
    db.add(
        Party(
            name=name.strip(),
            party_type=party_type.strip() or None,
            contact_info=contact_info.strip() or None,
        )
    )
    db.commit()
    return RedirectResponse("/parties?msg=Partie+ajout%C3%A9e", status_code=303)


@router.post("/{party_id}/toggle")
def toggle_party(party_id: int, db: Session = Depends(get_db)):
    party = db.get(Party, party_id)
    if party is None:
        raise HTTPException(404)
    party.active = not party.active
    db.add(party)
    db.commit()
    return RedirectResponse("/parties?msg=Mis+%C3%A0+jour", status_code=303)
