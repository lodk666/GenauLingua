"""add_unique_and_index_to_translation_reports

Revision ID: 7f7a5d79c7e7
Revises: c7c06112da81
Create Date: 2026-04-08 16:24:19.502275

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f7a5d79c7e7'
down_revision: Union[str, None] = 'c7c06112da81'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Удаляем возможные дубликаты перед добавлением constraint
    op.execute("""
        DELETE FROM translation_reports a
        USING translation_reports b
        WHERE a.id > b.id
          AND a.user_id = b.user_id
          AND a.word_id = b.word_id
    """)

    # Один юзер = один репорт на слово
    op.create_unique_constraint(
        'uq_translation_reports_user_word',
        'translation_reports',
        ['user_id', 'word_id']
    )

    # Индекс для быстрой фильтрации по статусу
    op.create_index(
        'ix_translation_reports_status',
        'translation_reports',
        ['status']
    )


def downgrade() -> None:
    op.drop_index('ix_translation_reports_status', table_name='translation_reports')
    op.drop_constraint('uq_translation_reports_user_word', 'translation_reports', type_='unique')