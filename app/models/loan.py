from __future__ import annotations

from typing import Optional

import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class LoanStatus(str, enum.Enum):
    ACTIVE = "active"
    PARTIALLY_RETURNED = "partially_returned"
    RETURNED = "returned"
    CANCELLED = "cancelled"


class Loan(Base):
    __tablename__ = "loan"

    id: Mapped[int] = mapped_column(primary_key=True)
    borrower_member_id: Mapped[int] = mapped_column(ForeignKey("team_member.id"))
    is_for_self: Mapped[bool] = mapped_column(Boolean, default=True)
    holder_contact_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("party_contact.id"), default=None
    )
    checkout_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    due_date: Mapped[Optional[date]] = mapped_column(Date, default=None)
    returned_date: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)
    status: Mapped[LoanStatus] = mapped_column(Enum(LoanStatus), default=LoanStatus.ACTIVE)
    notes: Mapped[Optional[str]] = mapped_column(String(1000), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    borrower: Mapped["TeamMember"] = relationship(foreign_keys=[borrower_member_id])
    holder_contact: Mapped[Optional["PartyContact"]] = relationship(foreign_keys=[holder_contact_id])
    lines: Mapped[list["LoanLine"]] = relationship(
        back_populates="loan", cascade="all, delete-orphan"
    )

    @property
    def holder_display(self) -> str:
        if self.is_for_self:
            return f"{self.borrower.full_name} (lui-même)"
        if self.holder_contact is not None:
            return f"{self.holder_contact.full_name} ({self.holder_contact.party.name})"
        return "?"

    @property
    def is_overdue(self) -> bool:
        if self.due_date is None or self.status == LoanStatus.RETURNED:
            return False
        return self.due_date < date.today()
