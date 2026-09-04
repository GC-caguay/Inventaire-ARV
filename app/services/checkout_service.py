from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.models import (
    ItemType,
    ItemUnit,
    KitComponent,
    Loan,
    LoanLine,
    LoanStatus,
    UnitStatus,
)


class CheckoutError(Exception):
    pass


@dataclass
class LineRequest:
    item_type_id: int
    quantity: int = 1
    item_unit_id: int | None = None
    is_from_kit: bool = False


def get_available_quantity(db: Session, item_type: ItemType) -> int:
    """Fungible stock available = total owned minus outstanding quantity on active/partial loans."""
    if item_type.is_serialized:
        raise ValueError("get_available_quantity only applies to fungible item types")
    total = item_type.total_quantity or 0
    lines = (
        db.query(LoanLine)
        .join(Loan)
        .filter(
            LoanLine.item_type_id == item_type.id,
            Loan.status.in_([LoanStatus.ACTIVE, LoanStatus.PARTIALLY_RETURNED]),
        )
        .all()
    )
    outstanding = sum(line.quantity_outstanding for line in lines)
    return total - outstanding


def expand_kit(db: Session, parent_item_type_id: int) -> list[KitComponent]:
    return (
        db.query(KitComponent)
        .filter(KitComponent.parent_item_type_id == parent_item_type_id)
        .all()
    )


def create_loan(
    db: Session,
    *,
    borrower_member_id: int,
    is_for_self: bool,
    holder_contact_id: int | None,
    due_date: date | None,
    notes: str | None,
    lines: list[LineRequest],
) -> Loan:
    if is_for_self:
        holder_contact_id = None
    elif not holder_contact_id:
        raise CheckoutError(
            "Préciser qui sera en possession (comité + membre du comité) quand ce n'est pas pour soi-même."
        )

    if not lines:
        raise CheckoutError("Ajouter au moins un item à sortir.")

    loan = Loan(
        borrower_member_id=borrower_member_id,
        is_for_self=is_for_self,
        holder_contact_id=holder_contact_id,
        due_date=due_date,
        notes=notes,
        status=LoanStatus.ACTIVE,
    )
    db.add(loan)

    for line_req in lines:
        item_type = db.get(ItemType, line_req.item_type_id)
        if item_type is None:
            raise CheckoutError(f"Item introuvable (id {line_req.item_type_id}).")

        if item_type.is_serialized:
            if not line_req.item_unit_id:
                raise CheckoutError(f"Choisir une unité précise pour {item_type.name}.")
            unit = db.get(ItemUnit, line_req.item_unit_id)
            if unit is None or unit.item_type_id != item_type.id:
                raise CheckoutError(f"Unité invalide pour {item_type.name}.")
            if unit.status != UnitStatus.IN_STOCK:
                raise CheckoutError(
                    f"{item_type.name} (série {unit.serial_number or unit.id}) n'est pas en stock."
                )
            unit.status = UnitStatus.OUT
            db.add(unit)
            db.add(
                LoanLine(
                    loan=loan,
                    item_type_id=item_type.id,
                    item_unit_id=unit.id,
                    quantity=1,
                    is_from_kit=line_req.is_from_kit,
                )
            )
        else:
            qty = line_req.quantity or 0
            if qty <= 0:
                raise CheckoutError(f"Quantité invalide pour {item_type.name}.")
            available = get_available_quantity(db, item_type)
            if qty > available:
                raise CheckoutError(
                    f"Seulement {available} {item_type.unit_label or 'unité(s)'} "
                    f"disponible(s) pour {item_type.name}."
                )
            db.add(
                LoanLine(
                    loan=loan,
                    item_type_id=item_type.id,
                    item_unit_id=None,
                    quantity=qty,
                    is_from_kit=line_req.is_from_kit,
                )
            )

    db.commit()
    db.refresh(loan)
    return loan
