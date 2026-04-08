"""add_translation_reports

Revision ID: c7c06112da81
Revises: 5b29968fea88
Create Date: 2026-04-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c7c06112da81'
down_revision: Union[str, None] = '5b29968fea88'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'translation_reports',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('word_id', sa.Integer(), nullable=False),
        sa.Column('quiz_session_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['word_id'], ['words.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['quiz_session_id'], ['quiz_sessions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_translation_reports_user_id', 'translation_reports', ['user_id'])
    op.create_index('ix_translation_reports_word_id', 'translation_reports', ['word_id'])


def downgrade() -> None:
    op.drop_index('ix_translation_reports_word_id', table_name='translation_reports')
    op.drop_index('ix_translation_reports_user_id', table_name='translation_reports')
    op.drop_table('translation_reports')