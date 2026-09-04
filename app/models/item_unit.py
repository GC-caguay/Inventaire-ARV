from __future__ import annotations

from typing import Optional

import enum
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UnitStatus(str, enum.Enum):
    IN_STOCK = "in_stock"
    OUT = "out"
    MAINTENANCE = "maintenance"
    LOST = "lost"
    RETIRED = "retired"


class ItemUnit(Base):
    __tablename__ = "item_unit"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_type_id: Mapped[int] = mapped_column(ForeignKey("item_type.id"))
    serial_number: Mapped[Optional[str]] = mapped_column(String(100), unique=True, default=None)
    status: Mapped[UnitStatus] = mapped_column(Enum(UnitStatus), default=UnitStatus.IN_STOCK)
    acquired_date: Mapped[Optional[date]] = mapped_column(Date, default=None)
    notes: Mapped[Optional[str]] = mapped_column(String(500), default=None)

    item_type: Mapped["ItemType"] = relationship(back_populates="units")
