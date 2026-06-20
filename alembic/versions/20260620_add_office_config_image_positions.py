"""add image position columns to office_config

Revision ID: c3d4e5f6a1b2
Revises: b2c3d4e5f6a1
Create Date: 2026-06-20
"""

import sqlalchemy as sa

from alembic import op

revision = "c3d4e5f6a1b2"
down_revision = "b2c3d4e5f6a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "office_config", sa.Column("hero_image_position", sa.String(20), nullable=True)
    )
    op.add_column(
        "office_config", sa.Column("about_image_position", sa.String(20), nullable=True)
    )
    op.add_column(
        "office_config",
        sa.Column("lawyer_image_position", sa.String(20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("office_config", "lawyer_image_position")
    op.drop_column("office_config", "about_image_position")
    op.drop_column("office_config", "hero_image_position")
