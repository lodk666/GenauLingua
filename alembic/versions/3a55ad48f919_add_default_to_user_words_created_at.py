"""add default to user_words.created_at

Revision ID: 3a55ad48f919
Revises: a699d3adb0db
Create Date: 2026-02-18 21:17:18.546545

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a55ad48f919'
down_revision: Union[str, None] = 'a699d3adb0db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column(
        "user_words",
        "created_at",
        server_default=sa.text("now()"),
    )


def downgrade():
    op.alter_column(
        "user_words",
        "created_at",
        server_default=None,
    )
