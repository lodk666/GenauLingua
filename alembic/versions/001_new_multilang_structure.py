"""Миграция: Новая структура БД с поддержкой многоязычности

Revision ID: 001_new_multilang_structure
Revises: 
Create Date: 2024-11-02
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_new_multilang_structure'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Применение миграции"""
    
    # Создание таблицы users
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('last_name', sa.String(length=255), nullable=True),
        sa.Column('level', sa.Enum('A1', 'A2', 'B1', 'B2', 'C1', 'C2', name='cefrlevel'), nullable=False),
        sa.Column('translation_mode', sa.Enum('DE_TO_RU', 'RU_TO_DE', 'DE_TO_UK', 'UK_TO_DE', name='translationmode'), nullable=False),
        sa.Column('interface_language', sa.String(length=2), nullable=False, server_default='ru'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Создание таблицы words
    op.create_table(
        'words',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('word_de', sa.String(length=255), nullable=False),
        sa.Column('article', sa.String(length=10), nullable=True),
        sa.Column('pos', sa.Enum('NOUN', 'VERB', 'ADJECTIVE', 'ADVERB', 'PHRASE', 'PRONOUN', 'PREPOSITION', 'CONJUNCTION', 'OTHER', name='partofspeech'), nullable=False),
        sa.Column('level', sa.Enum('A1', 'A2', 'B1', 'B2', 'C1', 'C2', name='cefrlevel'), nullable=False),
        sa.Column('translation_ru', sa.String(length=255), nullable=True),
        sa.Column('translation_uk', sa.String(length=255), nullable=True),
        sa.Column('example_de', sa.Text(), nullable=True),
        sa.Column('example_ru', sa.Text(), nullable=True),
        sa.Column('example_uk', sa.Text(), nullable=True),
        sa.Column('categories', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('times_shown', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('times_correct', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Создание индексов для words
    op.create_index('ix_words_word_de', 'words', ['word_de'])
    op.create_index('ix_words_level', 'words', ['level'])
    
    # Создание таблицы quiz_sessions
    op.create_table(
        'quiz_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('level', sa.Enum('A1', 'A2', 'B1', 'B2', 'C1', 'C2', name='cefrlevel'), nullable=False),
        sa.Column('translation_mode', sa.Enum('DE_TO_RU', 'RU_TO_DE', 'DE_TO_UK', 'UK_TO_DE', name='translationmode'), nullable=False),
        sa.Column('total_questions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('correct_answers', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Создание индекса для quiz_sessions
    op.create_index('ix_quiz_sessions_user_id', 'quiz_sessions', ['user_id'])
    
    # Создание таблицы quiz_questions
    op.create_table(
        'quiz_questions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('word_id', sa.Integer(), nullable=False),
        sa.Column('user_answer', sa.String(length=255), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('answered_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['quiz_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['word_id'], ['words.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Создание индексов для quiz_questions
    op.create_index('ix_quiz_questions_session_id', 'quiz_questions', ['session_id'])
    op.create_index('ix_quiz_questions_word_id', 'quiz_questions', ['word_id'])


def downgrade() -> None:
    """Откат миграции"""
    
    # Удаление таблиц
    op.drop_index('ix_quiz_questions_word_id', table_name='quiz_questions')
    op.drop_index('ix_quiz_questions_session_id', table_name='quiz_questions')
    op.drop_table('quiz_questions')
    
    op.drop_index('ix_quiz_sessions_user_id', table_name='quiz_sessions')
    op.drop_table('quiz_sessions')
    
    op.drop_index('ix_words_level', table_name='words')
    op.drop_index('ix_words_word_de', table_name='words')
    op.drop_table('words')
    
    op.drop_table('users')
    
    # Удаление enum типов
    sa.Enum(name='translationmode').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='cefrlevel').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='partofspeech').drop(op.get_bind(), checkfirst=True)