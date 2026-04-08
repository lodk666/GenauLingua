"""add_quiz_mode_and_category

Revision ID: 5b29968fea88
Revises: f1a2b3c4d5e6
Create Date: 2026-04-07 15:27:19.595070

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b29968fea88'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Создаём enum quizmode
    op.execute("CREATE TYPE quizmode AS ENUM ('level', 'category', 'all_words', 'difficult')")

    # 2. User: quiz_mode (с дефолтом для существующих юзеров) + quiz_category
    op.add_column('users', sa.Column(
        'quiz_mode',
        sa.Enum('level', 'category', 'all_words', 'difficult', name='quizmode'),
        nullable=False,
        server_default='level'
    ))
    op.add_column('users', sa.Column(
        'quiz_category', sa.String(length=100), nullable=True
    ))

    # 3. Word: category + frequency_rank + индексы
    op.add_column('words', sa.Column(
        'category', sa.String(length=100), nullable=True
    ))
    op.add_column('words', sa.Column(
        'frequency_rank', sa.Integer(), nullable=True
    ))
    op.create_index('ix_words_category', 'words', ['category'])
    op.create_index('ix_words_frequency_rank', 'words', ['frequency_rank'])

    # 4. QuizSession: quiz_mode + quiz_category (аналитика)
    op.add_column('quiz_sessions', sa.Column(
        'quiz_mode', sa.String(length=50), nullable=True
    ))
    op.add_column('quiz_sessions', sa.Column(
        'quiz_category', sa.String(length=100), nullable=True
    ))


def downgrade() -> None:
    # QuizSession
    op.drop_column('quiz_sessions', 'quiz_category')
    op.drop_column('quiz_sessions', 'quiz_mode')

    # Word
    op.drop_index('ix_words_frequency_rank', table_name='words')
    op.drop_index('ix_words_category', table_name='words')
    op.drop_column('words', 'frequency_rank')
    op.drop_column('words', 'category')

    # User
    op.drop_column('users', 'quiz_category')
    op.drop_column('users', 'quiz_mode')

    # Enum
    op.execute("DROP TYPE IF EXISTS quizmode")