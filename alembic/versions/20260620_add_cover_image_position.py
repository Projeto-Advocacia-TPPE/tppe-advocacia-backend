"""add cover_image_position to articles

Revision ID: a1b2c3d4e5f6
Revises: 20260618_add_user_updated_audit_action
Create Date: 2026-06-20
"""

import sqlalchemy as sa

from alembic import op

revision = "b2c3d4e5f6a1"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "articles", sa.Column("cover_image_position", sa.String(20), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("articles", "cover_image_position")
