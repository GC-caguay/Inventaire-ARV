from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Category, ItemType, ItemUnit, KitComponent, UnitStatus
from app.services.checkout_service import get_available_quantity
from app.templates_env import templates

router = APIRouter(prefix="/inventory")


@router.get("")
def list_inventory(
    request: Request,
    q: Optional[str] = None,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    query = (
        db.query(ItemType)
        .filter(ItemType.active == True)  # noqa: E712
        .options(joinedload(ItemType.category), joinedload(ItemType.units))
    )
    if q:
        query = query.filter(ItemType.name.ilike(f"%{q}%"))
    if category_id:
        query = query.filter(ItemType.category_id == category_id)
    item_types = query.order_by(ItemType.name).all()
    categories = db.query(Category).order_by(Category.name).all()

    availability = {
        it.id: get_available_quantity(db, it) for it in item_types if not it.is_serialized
    }

    return templates.TemplateResponse(
        "inventory/list.html",
        {
            "request": request,
            "item_types": item_types,
            "categories": categories,
            "availability": availability,
            "q": q or "",
            "category_id": category_id,
        },
    )


@router.get("/new")
def new_item_form(request: Request, db: Session = Depends(get_db)):
    categories = db.query(Category).order_by(Category.name).all()
    return templates.TemplateResponse(
        "inventory/item_form.html",
        {"request": request, "categories": categories, "item_type": None},
    )


@router.post("/new")
def create_item(
    name: str = Form(...),
    category_id: int = Form(...),
    description: str = Form(""),
    is_serialized: str = Form("true"),
    total_quantity: int = Form(0),
    unit_label: str = Form(""),
    initial_units: int = Form(0),
    db: Session = Depends(get_db),
):
    serialized = is_serialized == "true"
    item_type = ItemType(
        name=name.strip(),
        category_id=category_id,
        description=description.strip() or None,
        is_serialized=serialized,
        total_quantity=None if serialized else total_quantity,
        unit_label=unit_label.strip() or None,
    )
    db.add(item_type)
    db.flush()

    if serialized and initial_units > 0:
        for _ in range(initial_units):
            db.add(ItemUnit(item_type_id=item_type.id, status=UnitStatus.IN_STOCK))

    db.commit()
    return RedirectResponse(f"/inventory/{item_type.id}?msg=Item+cr%C3%A9%C3%A9", status_code=303)


@router.get("/{item_type_id}")
def item_detail(item_type_id: int, request: Request, db: Session = Depends(get_db)):
    item_type = db.get(ItemType, item_type_id)
    if item_type is None:
        raise HTTPException(404)
    kit_components = (
        db.query(KitComponent)
        .filter(KitComponent.parent_item_type_id == item_type_id)
        .options(joinedload(KitComponent.accessory_item_type))
        .all()
    )
    other_item_types = (
        db.query(ItemType)
        .filter(ItemType.active == True, ItemType.id != item_type_id)  # noqa: E712
        .order_by(ItemType.name)
        .all()
    )
    available_qty = None
    if not item_type.is_serialized:
        available_qty = get_available_quantity(db, item_type)

    return templates.TemplateResponse(
        "inventory/item_detail.html",
        {
            "request": request,
            "item_type": item_type,
            "kit_components": kit_components,
            "other_item_types": other_item_types,
            "available_qty": available_qty,
        },
    )


@router.get("/{item_type_id}/edit")
def edit_item_form(item_type_id: int, request: Request, db: Session = Depends(get_db)):
    item_type = db.get(ItemType, item_type_id)
    if item_type is None:
        raise HTTPException(404)
    categories = db.query(Category).order_by(Category.name).all()
    return templates.TemplateResponse(
        "inventory/item_form.html",
        {"request": request, "categories": categories, "item_type": item_type},
    )


@router.post("/{item_type_id}/edit")
def update_item(
    item_type_id: int,
    name: str = Form(...),
    category_id: int = Form(...),
    description: str = Form(""),
    total_quantity: int = Form(0),
    unit_label: str = Form(""),
    db: Session = Depends(get_db),
):
    item_type = db.get(ItemType, item_type_id)
    if item_type is None:
        raise HTTPException(404)
    item_type.name = name.strip()
    item_type.category_id = category_id
    item_type.description = description.strip() or None
    item_type.unit_label = unit_label.strip() or None
    if not item_type.is_serialized:
        item_type.total_quantity = total_quantity
    db.add(item_type)
    db.commit()
    return RedirectResponse(f"/inventory/{item_type_id}?msg=Item+mis+%C3%A0+jour", status_code=303)


@router.post("/{item_type_id}/delete")
def delete_item(item_type_id: int, db: Session = Depends(get_db)):
    item_type = db.get(ItemType, item_type_id)
    if item_type is None:
        raise HTTPException(404)
    item_type.active = False
    db.add(item_type)
    db.commit()
    return RedirectResponse("/inventory?msg=Item+archiv%C3%A9", status_code=303)


@router.post("/{item_type_id}/units/add")
def add_unit(item_type_id: int, serial_number: str = Form(""), db: Session = Depends(get_db)):
    item_type = db.get(ItemType, item_type_id)
    if item_type is None or not item_type.is_serialized:
        raise HTTPException(400, "Cet item n'est pas sérialisé.")
    db.add(
        ItemUnit(
            item_type_id=item_type_id,
            serial_number=serial_number.strip() or None,
            status=UnitStatus.IN_STOCK,
        )
    )
    db.commit()
    return RedirectResponse(f"/inventory/{item_type_id}?msg=Unit%C3%A9+ajout%C3%A9e", status_code=303)


@router.post("/{item_type_id}/units/{unit_id}/delete")
def delete_unit(item_type_id: int, unit_id: int, db: Session = Depends(get_db)):
    unit = db.get(ItemUnit, unit_id)
    if unit is None or unit.item_type_id != item_type_id:
        raise HTTPException(404)
    if unit.status == UnitStatus.OUT:
        raise HTTPException(400, "Impossible de retirer une unité actuellement sortie.")
    unit.status = UnitStatus.RETIRED
    db.add(unit)
    db.commit()
    return RedirectResponse(f"/inventory/{item_type_id}?msg=Unit%C3%A9+retir%C3%A9e", status_code=303)


@router.post("/{item_type_id}/kit/add")
def add_kit_component(
    item_type_id: int,
    accessory_item_type_id: int = Form(...),
    default_quantity: int = Form(1),
    db: Session = Depends(get_db),
):
    existing = (
        db.query(KitComponent)
        .filter(
            KitComponent.parent_item_type_id == item_type_id,
            KitComponent.accessory_item_type_id == accessory_item_type_id,
        )
        .first()
    )
    if existing:
        existing.default_quantity = default_quantity
        db.add(existing)
    else:
        db.add(
            KitComponent(
                parent_item_type_id=item_type_id,
                accessory_item_type_id=accessory_item_type_id,
                default_quantity=default_quantity,
            )
        )
    db.commit()
    return RedirectResponse(f"/inventory/{item_type_id}?msg=Accessoire+li%C3%A9", status_code=303)


@router.post("/{item_type_id}/kit/{kit_id}/delete")
def delete_kit_component(item_type_id: int, kit_id: int, db: Session = Depends(get_db)):
    kit = db.get(KitComponent, kit_id)
    if kit is None or kit.parent_item_type_id != item_type_id:
        raise HTTPException(404)
    db.delete(kit)
    db.commit()
    return RedirectResponse(f"/inventory/{item_type_id}?msg=Accessoire+retir%C3%A9", status_code=303)
