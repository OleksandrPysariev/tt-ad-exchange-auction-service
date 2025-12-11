from sqlalchemy import String, Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.meta import meta
from app.db.base import Base


class Supply(Base):
    __tablename__ = "supplies"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)  # the supply's name is its id
    bidders: Mapped[list["Bidder"]] = relationship(
        "Bidder",
        secondary=Table(
            "supply_bidder",
            meta,
            Column("supply_id", String, ForeignKey("supplies.id", ondelete="CASCADE"), primary_key=True),
            Column("bidder_id", String, ForeignKey("bidders.id", ondelete="CASCADE"), primary_key=True),
        ),
        back_populates="supplies",
    )

    def __repr__(self) -> str:
        return f"<Supply(id={self.id})>"
