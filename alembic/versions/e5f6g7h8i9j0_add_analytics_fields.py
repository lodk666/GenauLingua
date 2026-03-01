"""add analytics fields

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2026-03-01 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e5f6g7h8i9j0'
down_revision = 'd4e5f6g7h8i9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # User: добавляем last_quiz_date
    op.add_column('users', sa.Column('last_quiz_date', sa.Date(), nullable=True))

    # QuizSession: добавляем аналитические поля
    op.add_column('quiz_sessions', sa.Column('start_source', sa.String(50), nullable=True))
    op.add_column('quiz_sessions', sa.Column('exit_reason', sa.String(50), nullable=True))
    op.add_column('quiz_sessions', sa.Column('exit_at_question', sa.Integer(), server_default='0', nullable=False))

    # QuizQuestion: добавляем время ответа
    op.add_column('quiz_questions', sa.Column('response_time_seconds', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Откатываем изменения в обратном порядке
    op.drop_column('quiz_questions', 'response_time_seconds')
    op.drop_column('quiz_sessions', 'exit_at_question')
    op.drop_column('quiz_sessions', 'exit_reason')
    op.drop_column('quiz_sessions', 'start_source')
    op.drop_column('users', 'last_quiz_date')