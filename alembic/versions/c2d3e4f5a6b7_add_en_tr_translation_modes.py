"""add en and tr translation modes

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-02-28 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op


revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("ALTER TYPE translationmode ADD VALUE IF NOT EXISTS 'de_to_en'")
    op.execute("ALTER TYPE translationmode ADD VALUE IF NOT EXISTS 'en_to_de'")
    op.execute("ALTER TYPE translationmode ADD VALUE IF NOT EXISTS 'de_to_tr'")
    op.execute("ALTER TYPE translationmode ADD VALUE IF NOT EXISTS 'tr_to_de'")


def downgrade():
    # Postgres не поддерживает удаление значений из enum
    # Для отката нужно пересоздать тип — оставляем пустым
    pass