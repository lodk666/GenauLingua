"""add timestamps to user_words

Revision ID: a699d3adb0db
Revises: 88d0cdddb6f3
Create Date: 2026-02-18 22:12:43.974231

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a699d3adb0db'
down_revision: Union[str, None] = '88d0cdddb6f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "user_words",
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.add_column(
        "user_words",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.execute("""
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = now();
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    """)

    op.execute("""
    CREATE TRIGGER update_user_words_updated_at
    BEFORE UPDATE ON user_words
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
    """)

    op.alter_column("user_words", "created_at", server_default=None)


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS update_user_words_updated_at ON user_words;")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column;")

    op.drop_column("user_words", "updated_at")
    op.drop_column("user_words", "created_at")


