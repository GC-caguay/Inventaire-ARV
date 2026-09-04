from __future__ import annotations

from sqlalchemy.orm import Session, joinedload

from app.models import ItemType, Loan, LoanStatus, PartyContact
from app.services.checkout_service import get_available_quantity


def get_dashboard_stats(db: Session) -> dict:
    item_types = db.query(ItemType).filter(ItemType.active == True).all()  # noqa: E712

    serialized_in_stock = 0
    serialized_out = 0
    fungible_total = 0
    fungible_available = 0

    for it in item_types:
        if it.is_serialized:
            serialized_in_stock += it.units_in_stock
            serialized_out += it.units_out
        else:
            fungible_total += it.total_quantity or 0
            fungible_available += get_available_quantity(db, it)

    active_loans = get_active_loans(db)
    overdue = [loan for loan in active_loans if loan.is_overdue]

    return {
        "serialized_in_stock": serialized_in_stock,
        "serialized_out": serialized_out,
        "fungible_total": fungible_total,
        "fungible_available": fungible_available,
        "fungible_out": fungible_total - fungible_available,
        "active_loan_count": len(active_loans),
        "overdue_loans": overdue,
    }


def get_active_loans(db: Session) -> list[Loan]:
    return (
        db.query(Loan)
        .filter(Loan.status.in_([LoanStatus.ACTIVE, LoanStatus.PARTIALLY_RETURNED]))
        .options(
            joinedload(Loan.borrower),
            joinedload(Loan.holder_contact).joinedload(PartyContact.party),
        )
        .order_by(Loan.checkout_date.desc())
        .all()
    )
