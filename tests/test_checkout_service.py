from __future__ import annotations

import pytest

from app.models import Category, ItemType, ItemUnit, KitComponent, Party, TeamMember, UnitStatus
from app.services.checkout_service import (
    CheckoutError,
    LineRequest,
    create_loan,
    get_available_quantity,
)


def _make_camera(db):
    cat = Category(name="Caméras")
    db.add(cat)
    db.flush()
    camera_type = ItemType(name="Camera A", category_id=cat.id, is_serialized=True)
    db.add(camera_type)
    db.flush()
    unit = ItemUnit(item_type_id=camera_type.id, status=UnitStatus.IN_STOCK)
    db.add(unit)
    db.commit()
    return camera_type, unit


def _make_camera_with_battery_kit(db):
    cat = Category(name="Caméras")
    db.add(cat)
    db.flush()
    camera_type = ItemType(name="Camera A", category_id=cat.id, is_serialized=True)
    battery_type = ItemType(
        name="Pile AA", category_id=cat.id, is_serialized=False, total_quantity=10, unit_label="pile"
    )
    db.add_all([camera_type, battery_type])
    db.flush()

    camera_unit = ItemUnit(item_type_id=camera_type.id, status=UnitStatus.IN_STOCK)
    db.add(camera_unit)
    db.add(
        KitComponent(
            parent_item_type_id=camera_type.id,
            accessory_item_type_id=battery_type.id,
            default_quantity=1,
        )
    )
    db.commit()
    return camera_type, camera_unit, battery_type


def test_checkout_for_self_defaults_holder_to_borrower(db):
    camera_type, unit = _make_camera(db)
    member = TeamMember(full_name="Charles-Antoine")
    db.add(member)
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

    assert loan.holder_member_id is None
    assert loan.holder_party_id is None
    assert loan.holder_display == "Charles-Antoine (lui-même)"
    assert unit.status == UnitStatus.OUT


def test_checkout_for_third_party_requires_holder(db):
    camera_type, unit = _make_camera(db)
    member = TeamMember(full_name="Charles-Antoine")
    db.add(member)
    db.commit()

    with pytest.raises(CheckoutError):
        create_loan(
            db,
            borrower_member_id=member.id,
            is_for_self=False,
            holder_member_id=None,
            holder_party_id=None,
            due_date=None,
            notes=None,
            lines=[LineRequest(item_type_id=camera_type.id, item_unit_id=unit.id)],
        )


def test_checkout_for_third_party_sets_distinct_holder(db):
    camera_type, unit = _make_camera(db)
    member = TeamMember(full_name="Charles-Antoine")
    party = Party(name="Comité Promotion")
    db.add_all([member, party])
    db.commit()

    loan = create_loan(
        db,
        borrower_member_id=member.id,
        is_for_self=False,
        holder_member_id=None,
        holder_party_id=party.id,
        due_date=None,
        notes=None,
        lines=[LineRequest(item_type_id=camera_type.id, item_unit_id=unit.id)],
    )

    assert loan.borrower_member_id == member.id
    assert loan.holder_party_id == party.id
    assert loan.holder_display == "Comité Promotion"


def test_kit_line_qty_is_overridable_and_reduces_availability(db):
    camera_type, camera_unit, battery_type = _make_camera_with_battery_kit(db)
    member = TeamMember(full_name="Charles-Antoine")
    db.add(member)
    db.commit()

    loan = create_loan(
        db,
        borrower_member_id=member.id,
        is_for_self=True,
        holder_member_id=None,
        holder_party_id=None,
        due_date=None,
        notes=None,
        lines=[
            LineRequest(item_type_id=camera_type.id, item_unit_id=camera_unit.id),
            LineRequest(item_type_id=battery_type.id, quantity=3, is_from_kit=True),
        ],
    )

    battery_lines = [l for l in loan.lines if l.item_type_id == battery_type.id]
    assert len(battery_lines) == 1
    assert battery_lines[0].quantity == 3
    assert get_available_quantity(db, battery_type) == 7


def test_cannot_checkout_more_fungible_qty_than_available(db):
    cat = Category(name="Piles")
    db.add(cat)
    db.flush()
    battery_type = ItemType(
        name="Pile AA", category_id=cat.id, is_serialized=False, total_quantity=2, unit_label="pile"
    )
    member = TeamMember(full_name="Charles-Antoine")
    db.add_all([battery_type, member])
    db.commit()

    with pytest.raises(CheckoutError):
        create_loan(
            db,
            borrower_member_id=member.id,
            is_for_self=True,
            holder_member_id=None,
            holder_party_id=None,
            due_date=None,
            notes=None,
            lines=[LineRequest(item_type_id=battery_type.id, quantity=5)],
        )


def test_cannot_checkout_unit_already_out(db):
    cat = Category(name="Caméras")
    db.add(cat)
    db.flush()
    camera_type = ItemType(name="Camera A", category_id=cat.id, is_serialized=True)
    db.add(camera_type)
    db.flush()
    unit = ItemUnit(item_type_id=camera_type.id, status=UnitStatus.OUT)
    member = TeamMember(full_name="Charles-Antoine")
    db.add_all([unit, member])
    db.commit()

    with pytest.raises(CheckoutError):
        create_loan(
            db,
            borrower_member_id=member.id,
            is_for_self=True,
            holder_member_id=None,
            holder_party_id=None,
            due_date=None,
            notes=None,
            lines=[LineRequest(item_type_id=camera_type.id, item_unit_id=unit.id)],
        )
