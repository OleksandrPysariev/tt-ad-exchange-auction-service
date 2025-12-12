from sqlalchemy import String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Bidder(Base):
    __tablename__ = "bidders"
    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)  # the bidder's name is its id
    country: Mapped[str] = mapped_column(String(2), index=True, nullable=False)
    supplies: Mapped[list["Supply"]] = relationship(
        "Supply",
        secondary="supply_bidder",
        back_populates="bidders",
    )

    __table_args__ = (
        Index("ix_bidders_country", "country"),
        Index("idx_bidders_country_id", "country", "id"),
    )

    def __repr__(self) -> str:
        return f"<Bidder(id={self.id}, country={self.country})>"
