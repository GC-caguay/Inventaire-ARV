from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ItemType(Base):
    __tablename__ = "item_type"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(String(1000), default=None)
    is_serialized: Mapped[bool] = mapped_column(Boolean, default=True)
    total_quantity: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    unit_label: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    low_stock_threshold: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    photo_path: Mapped[Optional[str]] = mapped_column(String(500), default=None)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    category: Mapped["Category"] = relationship(back_populates="item_types")
    units: Mapped[list["ItemUnit"]] = relationship(
        back_populates="item_type", cascade="all, delete-orphan"
    )
    kit_components: Mapped[list["KitComponent"]] = relationship(
        foreign_keys="KitComponent.parent_item_type_id",
        back_populates="parent_item_type",
        cascade="all, delete-orphan",
    )

    @property
    def units_in_stock(self) -> int:
        return sum(1 for u in self.units if u.status.value == "in_stock")

    @property
    def units_out(self) -> int:
        return sum(1 for u in self.units if u.status.value == "out")
