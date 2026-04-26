"""init

Revision ID: 0001_init
Revises:
Create Date: 2026-04-26
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001_init"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "offers",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
    )
    op.create_table(
        "affiliates",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
    )
    op.create_table(
        "leads",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("country", sa.String(length=2), nullable=False),
        sa.Column("offer_id", sa.String(length=64), sa.ForeignKey("offers.id"), nullable=False),
        sa.Column(
            "affiliate_id",
            sa.String(length=64),
            sa.ForeignKey("affiliates.id"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_leads_created_at", "leads", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_leads_created_at", table_name="leads")
    op.drop_table("leads")
    op.drop_table("affiliates")
    op.drop_table("offers")
    