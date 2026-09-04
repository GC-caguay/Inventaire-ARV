from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.database import get_db
from app.models import ItemType, Loan, LoanStatus, Party, PartyContact, TeamMember, UnitStatus
from app.services.checkout_service import (
    CheckoutError,
    LineRequest,
    create_loan,
    expand_kit,
    get_available_quantity,
)
from app.services.dashboard_service import get_active_loans
from app.services.return_service import ReturnError, return_line
from app.templates_env import templates

router = APIRouter(prefix="/loans")


def _build_item_types_data(db: Session) -> dict:
    data = {}
    item_types = (
        db.query(ItemType)
        .filter(ItemType.active == True)  # noqa: E712
        .options(joinedload(ItemType.units))
        .order_by(ItemType.name)
        .all()
    )
    for it in item_types:
        kit = expand_kit(db, it.id)
        entry = {
            "id": it.id,
            "name": it.name,
            "is_serialized": it.is_serialized,
            "unit_label": it.unit_label or "unité",
            "kit": [
                {
                    "item_type_id": kc.accessory_item_type_id,
                    "name": kc.accessory_item_type.name,
                    "default_quantity": kc.default_quantity,
                }
                for kc in kit
            ],
        }
        if it.is_serialized:
            entry["units"] = [
                {"id": u.id, "label": u.serial_number or f"#{u.id}"}
                for u in it.units
                if u.status == UnitStatus.IN_STOCK
            ]
        else:
            entry["available_qty"] = get_available_quantity(db, it)
        data[it.id] = entry
    return data


def _checkout_context(request: Request, db: Session, error: Optional[str] = None) -> dict:
    members = (
        db.query(TeamMember)
        .filter(TeamMember.active == True)  # noqa: E712
        .order_by(TeamMember.full_name)
        .all()
    )
    parties = (
        db.query(Party)
        .filter(Party.active == True)  # noqa: E712
        .options(joinedload(Party.contacts))
        .order_by(Party.name)
        .all()
    )
    contacts_data = {
        str(p.id): [{"id": c.id, "full_name": c.full_name} for c in p.contacts if c.active]
        for p in parties
    }
    default_due = date.today() + timedelta(days=settings.default_loan_days)
    return {
        "request": request,
        "members": members,
        "parties": parties,
        "item_types_json": json.dumps(_build_item_types_data(db)),
        "contacts_json": json.dumps(contacts_data),
        "default_due": default_due.isoformat(),
        "error": error,
    }


def _resolve_holder_contact(db: Session, form) -> Optional[int]:
    party_raw = form.get("holder_party_id") or None
    new_party_name = (form.get("new_party_name") or "").strip()
    contact_raw = form.get("holder_contact_id") or None
    new_contact_name = (form.get("new_contact_name") or "").strip()

    if party_raw == "__new__" or (not party_raw and new_party_name):
        if not new_party_name:
            raise CheckoutError("Préciser le nom du nouveau comité.")
        party = Party(name=new_party_name)
        db.add(party)
        db.flush()
        party_id = party.id
    elif party_raw:
        party_id = int(party_raw)
    else:
        party_id = None

    if contact_raw == "__new__" or (not contact_raw and new_contact_name):
        if not new_contact_name:
            raise CheckoutError("Préciser le nom du membre du comité.")
        if party_id is None:
            raise CheckoutError("Choisir ou créer un comité avant d'ajouter un membre.")
        contact = PartyContact(party_id=party_id, full_name=new_contact_name)
        db.add(contact)
        db.flush()
        return contact.id
    if contact_raw:
        return int(contact_raw)
    return None


@router.get("/new")
def new_loan_form(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("loans/checkout_form.html", _checkout_context(request, db))


@router.post("/new")
async def create_loan_route(request: Request, db: Session = Depends(get_db)):
    form = await request.form()

    is_for_self = form.get("holder_mode", "self") == "self"
    due_date_raw = form.get("due_date")

    item_type_ids = form.getlist("line_item_type_id")
    item_unit_ids = form.getlist("line_item_unit_id")
    quantities = form.getlist("line_quantity")
    from_kit_flags = form.getlist("line_is_from_kit")

    lines = []
    for i, item_type_id in enumerate(item_type_ids):
        unit_id = item_unit_ids[i] if i < len(item_unit_ids) and item_unit_ids[i] else None
        qty = quantities[i] if i < len(quantities) and quantities[i] else "1"
        is_from_kit = from_kit_flags[i] if i < len(from_kit_flags) else "0"
        lines.append(
            LineRequest(
                item_type_id=int(item_type_id),
                quantity=int(qty),
                item_unit_id=int(unit_id) if unit_id else None,
                is_from_kit=is_from_kit == "1",
            )
        )

    try:
        holder_contact_id = None if is_for_self else _resolve_holder_contact(db, form)
        loan = create_loan(
            db,
            borrower_member_id=int(form["borrower_member_id"]),
            is_for_self=is_for_self,
            holder_contact_id=holder_contact_id,
            due_date=date.fromisoformat(due_date_raw) if due_date_raw else None,
            notes=form.get("notes") or None,
            lines=lines,
        )
    except CheckoutError as exc:
        db.rollback()
        return templates.TemplateResponse(
            "loans/checkout_form.html",
            _checkout_context(request, db, error=str(exc)),
            status_code=400,
        )

    return RedirectResponse(f"/loans/active?msg=Sortie+enregistr%C3%A9e+%23{loan.id}", status_code=303)


@router.get("/active")
def active_loans_view(request: Request, db: Session = Depends(get_db)):
    loans = get_active_loans(db)
    return templates.TemplateResponse("loans/who_has_what.html", {"request": request, "loans": loans})


@router.get("")
def loan_history(request: Request, status: Optional[str] = None, db: Session = Depends(get_db)):
    query = (
        db.query(Loan)
        .options(
            joinedload(Loan.borrower),
            joinedload(Loan.holder_contact).joinedload(PartyContact.party),
        )
        .order_by(Loan.checkout_date.desc())
    )
    if status:
        try:
            query = query.filter(Loan.status == LoanStatus(status))
        except ValueError:
            pass
    loans = query.all()
    return templates.TemplateResponse(
        "loans/history.html", {"request": request, "loans": loans, "status": status or ""}
    )


@router.get("/{loan_id}/return")
def return_form(loan_id: int, request: Request, db: Session = Depends(get_db)):
    loan = db.get(Loan, loan_id)
    if loan is None:
        raise HTTPException(404)
    return templates.TemplateResponse("loans/checkin_form.html", {"request": request, "loan": loan})


@router.post("/{loan_id}/return")
async def process_return(loan_id: int, request: Request, db: Session = Depends(get_db)):
    loan = db.get(Loan, loan_id)
    if loan is None:
        raise HTTPException(404)

    form = await request.form()
    errors = []
    for line in loan.lines:
        if line.quantity_outstanding <= 0:
            continue
        if not form.get(f"return_{line.id}"):
            continue
        condition = form.get(f"condition_{line.id}", "ok")
        qty = None
        if line.item_unit_id is None:
            qty_raw = form.get(f"quantity_{line.id}")
            qty = int(qty_raw) if qty_raw else line.quantity_outstanding
        try:
            return_line(db, line, quantity=qty, condition=condition)
        except ReturnError as exc:
            errors.append(str(exc))

    if errors:
        db.refresh(loan)
        return templates.TemplateResponse(
            "loans/checkin_form.html",
            {"request": request, "loan": loan, "error": " ".join(errors)},
            status_code=400,
        )

    return RedirectResponse("/loans/active?msg=Retour+enregistr%C3%A9", status_code=303)
