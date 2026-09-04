from __future__ import annotations

from typing import Optional

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LoanLineStatus(str, enum.Enum):
    ACTIVE = "active"
    PARTIAL = "partial"
    RETURNED = "returned"
    LOST = "lost"
    DAMAGED = "damaged"


class LoanLine(Base):
    __tablename__ = "loan_line"

    id: Mapped[int] = mapped_column(primary_key=True)
    loan_id: Mapped[int] = mapped_column(ForeignKey("loan.id"))
    item_type_id: Mapped[int] = mapped_column(ForeignKey("item_type.id"))
    item_unit_id: Mapped[Optional[int]] = mapped_column(ForeignKey("item_unit.id"), default=None)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    quantity_returned: Mapped[int] = mapped_column(Integer, default=0)
    returned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)
    line_status: Mapped[LoanLineStatus] = mapped_column(
        Enum(LoanLineStatus), default=LoanLineStatus.ACTIVE
    )
    is_from_kit: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(String(500), default=None)

    loan: Mapped["Loan"] = relationship(back_populates="lines")
    item_type: Mapped["ItemType"] = relationship()
    item_unit: Mapped[Optional["ItemUnit"]] = relationship()

    @property
    def quantity_outstanding(self) -> int:
        return self.quantity - self.quantity_returned
