from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Party(Base):
    __tablename__ = "party"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    party_type: Mapped[Optional[str]] = mapped_column(String(100), default=None)
    contact_info: Mapped[Optional[str]] = mapped_column(String(300), default=None)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    contacts: Mapped[list["PartyContact"]] = relationship(
        back_populates="party", cascade="all, delete-orphan"
    )
