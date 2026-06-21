"""add website_url to office_config

Revision ID: d4e5f6a7b2c3
Revises: c3d4e5f6a1b2
Create Date: 2026-06-21
"""

import sqlalchemy as sa

from alembic import op

revision = "d4e5f6a7b2c3"
down_revision = "c3d4e5f6a1b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "office_config", sa.Column("website_url", sa.String(500), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("office_config", "website_url")
