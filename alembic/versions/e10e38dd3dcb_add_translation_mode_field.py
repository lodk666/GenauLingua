"""add translation mode field

Revision ID: e10e38dd3dcb
Revises: 2f39cf587a31
Create Date: 2025-10-27 21:21:35.636024

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e10e38dd3dcb'
down_revision: Union[str, None] = '2f39cf587a31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
