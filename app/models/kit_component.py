from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class KitComponent(Base):
    __tablename__ = "kit_component"
    __table_args__ = (UniqueConstraint("parent_item_type_id", "accessory_item_type_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_item_type_id: Mapped[int] = mapped_column(ForeignKey("item_type.id"))
    accessory_item_type_id: Mapped[int] = mapped_column(ForeignKey("item_type.id"))
    default_quantity: Mapped[int] = mapped_column(Integer, default=1)
    notes: Mapped[Optional[str]] = mapped_column(String(500), default=None)

    parent_item_type: Mapped["ItemType"] = relationship(
        foreign_keys=[parent_item_type_id], back_populates="kit_components"
    )
    accessory_item_type: Mapped["ItemType"] = relationship(foreign_keys=[accessory_item_type_id])
