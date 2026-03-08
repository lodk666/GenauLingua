"""fix_enum_uppercase_values

Revision ID: aad3c50ea59b
Revises: 36f18cbb9329
Create Date: 2026-03-07

"""
from typing import Sequence, Union

from alembic import op

revision: str = 'aad3c50ea59b'
down_revision: Union[str, None] = '36f18cbb9329'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE translationmode ADD VALUE IF NOT EXISTS 'DE_TO_EN'")
    op.execute("ALTER TYPE translationmode ADD VALUE IF NOT EXISTS 'EN_TO_DE'")
    op.execute("ALTER TYPE translationmode ADD VALUE IF NOT EXISTS 'DE_TO_TR'")
    op.execute("ALTER TYPE translationmode ADD VALUE IF NOT EXISTS 'TR_TO_DE'")


def downgrade() -> None:
    pass