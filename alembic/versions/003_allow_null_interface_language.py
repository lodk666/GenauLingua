"""allow null interface_language

Revision ID: 003_allow_null
Revises: 002_add_user_word_stats
Create Date: 2026-02-17

"""
from alembic import op
import sqlalchemy as sa

revision = '003_allow_null'
down_revision = '002_add_user_word_stats'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.alter_column('users', 'interface_language',
                    existing_type=sa.String(),
                    nullable=True,
                    server_default=None)

def downgrade() -> None:
    op.alter_column('users', 'interface_language',
                    existing_type=sa.String(),
                    nullable=False,
                    server_default='ru')