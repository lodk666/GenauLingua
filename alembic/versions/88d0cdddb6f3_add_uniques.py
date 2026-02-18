"""add_uniques

Revision ID: 88d0cdddb6f3
Revises: 2e31b671aa69
Create Date: 2026-02-18 21:06:28.510875

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '88d0cdddb6f3'
down_revision: Union[str, None] = '2e31b671aa69'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_unique_constraint(
        "uq_words_word_de_level",
        "words",
        ["word_de", "level"]
    )

    op.create_unique_constraint(
        "uq_user_words_user_id_word_id",
        "user_words",
        ["user_id", "word_id"]
    )


def downgrade():
    op.drop_constraint("uq_user_words_user_id_word_id", "user_words", type_="unique")
    op.drop_constraint("uq_words_word_de_level", "words", type_="unique")
