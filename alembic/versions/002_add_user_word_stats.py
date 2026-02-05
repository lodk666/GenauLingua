"""Миграция: поля статистики для user_words

Revision ID: 002_add_user_word_stats
Revises: 001_new_multilang_structure
Create Date: 2025-02-14
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "002_add_user_word_stats"
down_revision: Union[str, None] = "001_new_multilang_structure"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Применение миграции"""
    op.add_column(
        "user_words",
        sa.Column("times_shown", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "user_words",
        sa.Column("times_correct", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    """Откат миграции"""
    op.drop_column("user_words", "times_correct")
    op.drop_column("user_words", "times_shown")
