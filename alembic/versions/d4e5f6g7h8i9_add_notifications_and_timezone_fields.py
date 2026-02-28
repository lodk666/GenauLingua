"""add notifications and timezone fields

Revision ID: d4e5f6g7h8i9
Revises: c2d3e4f5a6b7
Create Date: 2026-02-28 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd4e5f6g7h8i9'
down_revision: Union[str, None] = 'c2d3e4f5a6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # === ЯЗЫКИ И ЛОКАЛИЗАЦИЯ ===
    op.add_column('users', sa.Column('telegram_language', sa.String(10), nullable=True))

    # === TIMEZONE ===
    op.add_column('users', sa.Column('timezone', sa.String(50), nullable=False, server_default='Europe/Berlin'))
    op.add_column('users', sa.Column('utc_offset', sa.String(10), nullable=True))

    # === ВРЕМЯ АКТИВНОСТИ ===
    op.add_column('users', sa.Column('first_quiz_at', sa.DateTime(), nullable=True))
    # last_active_at будем обновлять при каждой активности
    op.add_column('users', sa.Column('last_active_at', sa.DateTime(), nullable=True,
                                     server_default=sa.text('CURRENT_TIMESTAMP')))

    # === НАПОМИНАНИЯ ===
    op.add_column('users', sa.Column('notifications_enabled', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('notification_time', sa.String(5), nullable=False, server_default='20:00'))
    op.add_column('users', sa.Column('notification_days', postgresql.ARRAY(sa.Integer()), nullable=False,
                                     server_default='{0,1,2,3,4,5,6}'))
    op.add_column('users', sa.Column('last_notification_sent', sa.DateTime(), nullable=True))

    # === НАСТРОЙКИ ВИКТОРИНЫ ===
    op.add_column('users', sa.Column('quiz_word_count', sa.Integer(), nullable=False, server_default='25'))


def downgrade():
    # Удаляем колонки в обратном порядке
    op.drop_column('users', 'quiz_word_count')
    op.drop_column('users', 'last_notification_sent')
    op.drop_column('users', 'notification_days')
    op.drop_column('users', 'notification_time')
    op.drop_column('users', 'notifications_enabled')
    op.drop_column('users', 'last_active_at')
    op.drop_column('users', 'first_quiz_at')
    op.drop_column('users', 'utc_offset')
    op.drop_column('users', 'timezone')
    op.drop_column('users', 'telegram_language')