from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Party, PartyContact
from app.templates_env import render

router = APIRouter(prefix="/parties")


@router.get("")
def list_parties(request: Request, db: Session = Depends(get_db)):
    parties = (
        db.query(Party)
        .options(joinedload(Party.contacts))
        .order_by(Party.active.desc(), Party.name)
        .all()
    )
    return render(request, "parties/list.html", parties=parties)


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
    return RedirectResponse("/parties?msg=Comit%C3%A9+ajout%C3%A9", status_code=303)


@router.post("/{party_id}/toggle")
def toggle_party(party_id: int, db: Session = Depends(get_db)):
    party = db.get(Party, party_id)
    if party is None:
        raise HTTPException(404)
    party.active = not party.active
    db.add(party)
    db.commit()
    return RedirectResponse("/parties?msg=Mis+%C3%A0+jour", status_code=303)


@router.get("/{party_id}")
def party_detail(party_id: int, request: Request, db: Session = Depends(get_db)):
    party = db.get(Party, party_id)
    if party is None:
        raise HTTPException(404)
    return render(request, "parties/detail.html", party=party)


@router.post("/{party_id}/contacts/add")
def add_contact(party_id: int, full_name: str = Form(...), db: Session = Depends(get_db)):
    party = db.get(Party, party_id)
    if party is None:
        raise HTTPException(404)
    db.add(PartyContact(party_id=party_id, full_name=full_name.strip()))
    db.commit()
    return RedirectResponse(f"/parties/{party_id}?msg=Membre+ajout%C3%A9", status_code=303)


@router.post("/{party_id}/contacts/{contact_id}/toggle")
def toggle_contact(party_id: int, contact_id: int, db: Session = Depends(get_db)):
    contact = db.get(PartyContact, contact_id)
    if contact is None or contact.party_id != party_id:
        raise HTTPException(404)
    contact.active = not contact.active
    db.add(contact)
    db.commit()
    return RedirectResponse(f"/parties/{party_id}?msg=Mis+%C3%A0+jour", status_code=303)
