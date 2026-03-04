"""add_monthly_system

Revision ID: 36f18cbb9329
Revises: e5f6g7h8i9j0
Create Date: 2026-03-04 14:52:31.099881

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '36f18cbb9329'
down_revision: Union[str, None] = 'e5f6g7h8i9j0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================================================
    # МЕСЯЧНАЯ СИСТЕМА РЕЙТИНГА
    # ========================================================================

    # 1. Таблица monthly_seasons (месячные сезоны)
    op.create_table(
        'monthly_seasons',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('winners_finalized', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. Таблица monthly_stats (статистика за месяц)
    op.create_table(
        'monthly_stats',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('season_id', sa.Integer(), nullable=False),

        # Основные метрики
        sa.Column('monthly_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('monthly_quizzes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('monthly_reverse', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('monthly_words', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('monthly_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('monthly_avg_percent', sa.Integer(), nullable=False, server_default='0'),

        # Для расчёта среднего
        sa.Column('total_correct', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_questions', sa.Integer(), nullable=False, server_default='0'),

        # Финальный ранг
        sa.Column('final_rank', sa.Integer(), nullable=True),

        # Служебные
        sa.Column('last_quiz_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),

        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['season_id'], ['monthly_seasons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Индексы для быстрых запросов
    op.create_index('ix_monthly_stats_user_id', 'monthly_stats', ['user_id'])
    op.create_index('ix_monthly_stats_season_id', 'monthly_stats', ['season_id'])
    op.create_index('ix_monthly_stats_score', 'monthly_stats', ['monthly_score'])

    # Уникальность: один юзер - одна запись на сезон
    op.create_unique_constraint(
        'uq_monthly_stats_user_season',
        'monthly_stats',
        ['user_id', 'season_id']
    )

    # 3. Таблица monthly_quiz_events (идемпотентность викторин)
    op.create_table(
        'monthly_quiz_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('quiz_session_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('season_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Уникальность: одна викторина учитывается только раз
    op.create_unique_constraint(
        'uq_quiz_event_session',
        'monthly_quiz_events',
        ['quiz_session_id']
    )

    op.create_index('ix_monthly_quiz_events_user_id', 'monthly_quiz_events', ['user_id'])
    op.create_index('ix_monthly_quiz_events_season_id', 'monthly_quiz_events', ['season_id'])

    # 4. Таблица win_streaks (серия побед)
    op.create_table(
        'win_streaks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('current_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('best_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_wins', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_win_season', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),

        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Уникальность: один юзер - одна запись стрика
    op.create_unique_constraint('uq_win_streak_user', 'win_streaks', ['user_id'])

    # 5. Таблица monthly_awards (награды)
    op.create_table(
        'monthly_awards',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('season_id', sa.Integer(), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('award_type', sa.String(50), nullable=False),  # gold, silver, bronze, top10
        sa.Column('lifetime_bonus', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),

        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['season_id'], ['monthly_seasons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_monthly_awards_user_id', 'monthly_awards', ['user_id'])
    op.create_index('ix_monthly_awards_season_id', 'monthly_awards', ['season_id'])

    # 6. Добавляем поля в таблицу users для lifetime системы
    op.add_column('users', sa.Column('lifetime_score', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('best_streak_days', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('total_monthly_wins', sa.Integer(), nullable=False, server_default='0'))

    # 7. Добавляем поля в quiz_sessions для аналитики (если ещё нет)
    # Эти поля уже добавлены в миграции e5f6g7h8i9j0, но на всякий случай проверим
    # op.add_column('quiz_sessions', sa.Column('start_source', sa.String(50), nullable=True))
    # op.add_column('quiz_sessions', sa.Column('exit_reason', sa.String(50), nullable=True))
    # op.add_column('quiz_sessions', sa.Column('exit_at_question', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    # Откат в обратном порядке

    # Удаляем поля из users
    op.drop_column('users', 'total_monthly_wins')
    op.drop_column('users', 'best_streak_days')
    op.drop_column('users', 'lifetime_score')

    # Удаляем таблицы
    op.drop_index('ix_monthly_awards_season_id', 'monthly_awards')
    op.drop_index('ix_monthly_awards_user_id', 'monthly_awards')
    op.drop_table('monthly_awards')

    op.drop_constraint('uq_win_streak_user', 'win_streaks', type_='unique')
    op.drop_table('win_streaks')

    op.drop_index('ix_monthly_quiz_events_season_id', 'monthly_quiz_events')
    op.drop_index('ix_monthly_quiz_events_user_id', 'monthly_quiz_events')
    op.drop_constraint('uq_quiz_event_session', 'monthly_quiz_events', type_='unique')
    op.drop_table('monthly_quiz_events')

    op.drop_constraint('uq_monthly_stats_user_season', 'monthly_stats', type_='unique')
    op.drop_index('ix_monthly_stats_score', 'monthly_stats')
    op.drop_index('ix_monthly_stats_season_id', 'monthly_stats')
    op.drop_index('ix_monthly_stats_user_id', 'monthly_stats')
    op.drop_table('monthly_stats')

    op.drop_table('monthly_seasons')