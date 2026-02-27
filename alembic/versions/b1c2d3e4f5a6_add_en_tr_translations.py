"""add en and tr translations to words

Revision ID: b1c2d3e4f5a6
Revises: a699d3adb0db
Create Date: 2026-02-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = '3a55ad48f919'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('words', sa.Column('translation_en', sa.Text(), nullable=True))
    op.add_column('words', sa.Column('example_en', sa.Text(), nullable=True))
    op.add_column('words', sa.Column('translation_tr', sa.Text(), nullable=True))
    op.add_column('words', sa.Column('example_tr', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('words', 'example_tr')
    op.drop_column('words', 'translation_tr')
    op.drop_column('words', 'example_en')
    op.drop_column('words', 'translation_en')