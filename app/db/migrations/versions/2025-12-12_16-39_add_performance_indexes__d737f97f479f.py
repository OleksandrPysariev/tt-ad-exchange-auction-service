"""add_performance_indexes

Revision ID: d737f97f479f
Revises: db4ba6e6734b
Create Date: 2025-12-12 16:39:34.890998

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd737f97f479f'
down_revision: Union[str, None] = 'db4ba6e6734b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add performance indexes."""
    # Critical: Index on supply_bidder.bidder_id for reverse lookups
    # The composite PK (supply_id, bidder_id) doesn't help queries filtering by bidder_id alone
    op.create_index(
        "idx_supply_bidder_bidder",
        "supply_bidder",
        ["bidder_id"],
        unique=False
    )

    # Beneficial: Composite index on bidders(country, id) for common query patterns
    # This optimizes queries that filter by country and need bidder IDs
    op.create_index(
        "idx_bidders_country_id",
        "bidders",
        ["country", "id"],
        unique=False
    )

    # Optional: Explicit index on supply_bidder.supply_id for completeness
    # (Less critical as composite PK index can be used, but makes intent clear)
    op.create_index(
        "idx_supply_bidder_supply",
        "supply_bidder",
        ["supply_id"],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema - Remove performance indexes."""
    op.drop_index("idx_supply_bidder_supply", table_name="supply_bidder")
    op.drop_index("idx_bidders_country_id", table_name="bidders")
    op.drop_index("idx_supply_bidder_bidder", table_name="supply_bidder")
