from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PartyContact(Base):
    """Une personne précise au sein d'un comité/tiers (ex. un membre du Comité Promotion)."""

    __tablename__ = "party_contact"

    id: Mapped[int] = mapped_column(primary_key=True)
    party_id: Mapped[int] = mapped_column(ForeignKey("party.id"))
    full_name: Mapped[str] = mapped_column(String(200))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    party: Mapped["Party"] = relationship(back_populates="contacts")
