"""enable_notifications_for_existing_users

Revision ID: 9194af87e5d4
Revises: aad3c50ea59b
Create Date: 2026-03-08

"""
from typing import Sequence, Union

from alembic import op

revision: str = '9194af87e5d4'
down_revision: Union[str, None] = 'aad3c50ea59b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        UPDATE users
        SET notifications_enabled = true,
            notification_time = '14:00',
            notification_days = '{0,1,2,3,4,5,6}'
        WHERE notifications_enabled = false
    """)


def downgrade() -> None:
    pass