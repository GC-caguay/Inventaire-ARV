from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models import ItemUnit, Loan, LoanLine, LoanLineStatus, LoanStatus, UnitStatus


class ReturnError(Exception):
    pass


_CONDITION_TO_UNIT_STATUS = {
    "ok": UnitStatus.IN_STOCK,
    "damaged": UnitStatus.MAINTENANCE,
    "lost": UnitStatus.LOST,
}

_CONDITION_TO_LINE_STATUS = {
    "ok": LoanLineStatus.RETURNED,
    "damaged": LoanLineStatus.DAMAGED,
    "lost": LoanLineStatus.LOST,
}


def return_line(db: Session, line: LoanLine, *, quantity: int | None, condition: str) -> LoanLine:
    if condition not in _CONDITION_TO_UNIT_STATUS:
        raise ReturnError(f"État de retour invalide : {condition}")

    if line.item_unit_id is not None:
        # Matériel sérialisé : l'unité complète revient en un seul geste.
        line.quantity_returned = line.quantity
        line.returned_at = datetime.utcnow()
        line.line_status = _CONDITION_TO_LINE_STATUS[condition]
        unit = db.get(ItemUnit, line.item_unit_id)
        if unit is not None:
            unit.status = _CONDITION_TO_UNIT_STATUS[condition]
            db.add(unit)
    else:
        qty = quantity if quantity is not None else line.quantity_outstanding
        if qty < 0 or qty > line.quantity_outstanding:
            raise ReturnError("Quantité retournée invalide.")
        line.quantity_returned += qty
        if line.quantity_returned >= line.quantity:
            line.returned_at = datetime.utcnow()
            line.line_status = _CONDITION_TO_LINE_STATUS[condition]
        elif line.quantity_returned > 0:
            line.line_status = LoanLineStatus.PARTIAL

    db.add(line)
    recompute_loan_status(db, line.loan)
    db.commit()
    db.refresh(line)
    return line


def recompute_loan_status(db: Session, loan: Loan) -> None:
    lines = loan.lines
    if not lines:
        return
    if all(l.quantity_returned >= l.quantity for l in lines):
        loan.status = LoanStatus.RETURNED
        loan.returned_date = datetime.utcnow()
    elif any(l.quantity_returned > 0 for l in lines):
        loan.status = LoanStatus.PARTIALLY_RETURNED
    else:
        loan.status = LoanStatus.ACTIVE
    db.add(loan)
