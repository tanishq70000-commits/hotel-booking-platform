"""Initial schema with btree_gist and exclusion constraint.

Revision ID: 001_initial
Revises:
Create Date: 2026-11-11 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Enable btree_gist extension (required for GiST indexing on integer + daterange)
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")

    # 2. Create rooms table
    op.create_table(
        "rooms",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("number", sa.String(length=32), nullable=False),
        sa.Column("room_type", sa.String(length=64), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("number"),
    )
    op.create_index("ix_rooms_number", "rooms", ["number"], unique=False)
    op.create_index("ix_rooms_room_type", "rooms", ["room_type"], unique=False)

    # 3. Create reservations table
    op.create_table(
        "reservations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("reference", sa.String(length=32), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("guest_name", sa.String(length=128), nullable=False),
        sa.Column("guest_email", sa.String(length=128), nullable=False),
        sa.Column("check_in", sa.Date(), nullable=False),
        sa.Column("check_out", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="CONFIRMED", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reference"),
        sa.CheckConstraint("check_out > check_in", name="check_valid_date_range"),
    )
    op.create_index("ix_reservations_reference", "reservations", ["reference"], unique=False)
    op.create_index("ix_reservations_room_id", "reservations", ["room_id"], unique=False)
    op.create_index("ix_reservations_check_in", "reservations", ["check_in"], unique=False)
    op.create_index("ix_reservations_check_out", "reservations", ["check_out"], unique=False)

    # 4. PostgreSQL GiST exclusion constraint against overlapping stays
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            ALTER TABLE reservations
            ADD CONSTRAINT exclude_overlapping_confirmed_reservations
            EXCLUDE USING gist (
                room_id WITH =,
                daterange(check_in, check_out, '[)') WITH &&
            )
            WHERE (status = 'CONFIRMED');
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            "ALTER TABLE reservations DROP CONSTRAINT IF EXISTS exclude_overlapping_confirmed_reservations;"
        )

    op.drop_table("reservations")
    op.drop_table("rooms")
