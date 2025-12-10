from sqlalchemy import String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base


class Bidder(Base):
    __tablename__ = "bidders"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    country: Mapped[str] = mapped_column(String(2), index=True, nullable=False)

    # Relationship to supplies
    supplies: Mapped[list["Supply"]] = relationship(
        "Supply",
        secondary="supply_bidder",
        back_populates="bidders",
    )

    __table_args__ = (
        Index("ix_bidders_country", "country"),
    )

    def __repr__(self) -> str:
        return f"<Bidder(id={self.id}, country={self.country})>"