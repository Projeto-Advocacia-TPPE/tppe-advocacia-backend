"""add USER_UPDATED to auditaction enum

Revision ID: a1b2c3d4e5f6
Revises: e3aaec7424dc
Create Date: 2026-06-18 00:00:00.000000+00:00

"""

from collections.abc import Sequence

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "e3aaec7424dc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'USER_UPDATED'")


def downgrade() -> None:
    # PostgreSQL não permite remover valores de um enum sem recriar o tipo.
    # Para reverter, é necessário dropar e recriar o tipo manualmente se não
    # houver nenhuma linha com USER_UPDATED na tabela.
    pass
