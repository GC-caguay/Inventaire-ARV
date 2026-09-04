from __future__ import annotations

from app.models import Category, ItemType, ItemUnit, LoanLineStatus, LoanStatus, TeamMember, UnitStatus
from app.services.checkout_service import LineRequest, create_loan
from app.services.return_service import return_line


def _setup_fungible_loan(db, total, qty_out):
    cat = Category(name="Piles")
    db.add(cat)
    db.flush()
    battery_type = ItemType(
        name="Pile AA", category_id=cat.id, is_serialized=False, total_quantity=total, unit_label="pile"
    )
    member = TeamMember(full_name="Charles-Antoine")
    db.add_all([battery_type, member])
    db.commit()

    loan = create_loan(
        db,
        borrower_member_id=member.id,
        is_for_self=True,
        holder_member_id=None,
        holder_party_id=None,
        due_date=None,
        notes=None,
        lines=[LineRequest(item_type_id=battery_type.id, quantity=qty_out)],
    )
    return loan


def _setup_serialized_loan(db):
    cat = Category(name="Caméras")
    db.add(cat)
    db.flush()
    camera_type = ItemType(name="Camera A", category_id=cat.id, is_serialized=True)
    db.add(camera_type)
    db.flush()
    unit = ItemUnit(item_type_id=camera_type.id, status=UnitStatus.IN_STOCK)
    member = TeamMember(full_name="Charles-Antoine")
    db.add_all([unit, member])
    db.commit()

    loan = create_loan(
        db,
        borrower_member_id=member.id,
        is_for_self=True,
        holder_member_id=None,
        holder_party_id=None,
        due_date=None,
        notes=None,
        lines=[LineRequest(item_type_id=camera_type.id, item_unit_id=unit.id)],
    )
    return loan, unit


def test_partial_return_keeps_loan_partially_returned(db):
    loan = _setup_fungible_loan(db, total=10, qty_out=5)
    line = loan.lines[0]

    return_line(db, line, quantity=2, condition="ok")

    db.refresh(loan)
    db.refresh(line)
    assert line.quantity_returned == 2
    assert line.line_status == LoanLineStatus.PARTIAL
    assert loan.status == LoanStatus.PARTIALLY_RETURNED


def test_full_return_closes_loan(db):
    loan = _setup_fungible_loan(db, total=10, qty_out=3)
    line = loan.lines[0]

    return_line(db, line, quantity=3, condition="ok")

    db.refresh(loan)
    assert loan.status == LoanStatus.RETURNED
    assert loan.returned_date is not None


def test_second_partial_return_completes_the_loan(db):
    loan = _setup_fungible_loan(db, total=10, qty_out=5)
    line = loan.lines[0]

    return_line(db, line, quantity=2, condition="ok")
    db.refresh(line)
    return_line(db, line, quantity=3, condition="ok")

    db.refresh(loan)
    db.refresh(line)
    assert line.quantity_returned == 5
    assert loan.status == LoanStatus.RETURNED


def test_serialized_return_sets_unit_status_by_condition(db):
    loan, unit = _setup_serialized_loan(db)
    line = loan.lines[0]

    return_line(db, line, quantity=None, condition="damaged")

    db.refresh(unit)
    db.refresh(loan)
    assert unit.status == UnitStatus.MAINTENANCE
    assert loan.status == LoanStatus.RETURNED
