"""fix language selection - make interface_language and translation_mode nullable

Revision ID: f1a2b3c4d5e6
Revises: 9194af87e5d4
Create Date: 2026-04-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = '9194af87e5d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Разрешаем NULL для новых юзеров (до выбора языка)
    op.alter_column('users', 'interface_language',
                    existing_type=sa.String(2),
                    nullable=True,
                    server_default=None)

    op.alter_column('users', 'translation_mode',
                    existing_type=sa.Enum('DE_TO_RU', 'RU_TO_DE', 'DE_TO_UK', 'UK_TO_DE',
                                          'DE_TO_EN', 'EN_TO_DE', 'DE_TO_TR', 'TR_TO_DE',
                                          name='translationmode'),
                    nullable=True,
                    server_default=None)


def downgrade() -> None:
    # Сначала заполняем NULL значения дефолтами
    op.execute("UPDATE users SET interface_language = 'ru' WHERE interface_language IS NULL")
    op.execute("UPDATE users SET translation_mode = 'DE_TO_RU' WHERE translation_mode IS NULL")

    op.alter_column('users', 'interface_language',
                    existing_type=sa.String(2),
                    nullable=False,
                    server_default='ru')

    op.alter_column('users', 'translation_mode',
                    existing_type=sa.Enum('DE_TO_RU', 'RU_TO_DE', 'DE_TO_UK', 'UK_TO_DE',
                                          'DE_TO_EN', 'EN_TO_DE', 'DE_TO_TR', 'TR_TO_DE',
                                          name='translationmode'),
                    nullable=False,
                    server_default='DE_TO_RU')