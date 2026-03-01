from datetime import datetime, date
from sqlalchemy import Date
from typing import List, Optional
import sqlalchemy as sa

from sqlalchemy import (
    BigInteger, String, Boolean, DateTime, Integer,
    ForeignKey, Text, Enum as SQLEnum, Float
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY
from app.database.enums import CEFRLevel, TranslationMode
import enum


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(255))
    first_name: Mapped[Optional[str]] = mapped_column(String(255))
    last_name: Mapped[Optional[str]] = mapped_column(String(255))

    # Статистика
    last_active_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    words_learned: Mapped[int] = mapped_column(Integer, default=0)
    quizzes_passed: Mapped[int] = mapped_column(Integer, default=0)
    success_rate: Mapped[int] = mapped_column(Integer, default=0)

    # 🆕 МЕСЯЧНАЯ СИСТЕМА
    lifetime_score: Mapped[int] = mapped_column(Integer, default=0)
    best_streak_days: Mapped[int] = mapped_column(Integer, default=0)
    total_monthly_wins: Mapped[int] = mapped_column(Integer, default=0)

    # Настройки
    level: Mapped[CEFRLevel] = mapped_column(SQLEnum(CEFRLevel), default=CEFRLevel.A1)
    translation_mode: Mapped[TranslationMode] = mapped_column(SQLEnum(TranslationMode),
                                                              default=TranslationMode.DE_TO_RU)
    interface_language: Mapped[str] = mapped_column(String(2), default="ru")
    # Notifications / timezone
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    notification_time: Mapped[Optional[str]] = mapped_column("notification_time", String(5), nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    anchor_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    # Relationships
    quiz_sessions: Mapped[List["QuizSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # 🆕 RELATIONSHIPS ДЛЯ МЕСЯЧНОЙ СИСТЕМЫ
    monthly_stats: Mapped[List["MonthlyStats"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    awards: Mapped[List["MonthlyAward"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    win_streak: Mapped[Optional["WinStreak"]] = relationship(
        back_populates="user",
        uselist=False
    )

    @property
    def display_name(self) -> str:
        """Отображаемое имя пользователя"""
        if self.username:
            return f"@{self.username}"
        elif self.first_name:
            return self.first_name
        else:
            return f"User {self.id}"

    def calculate_lifetime_score(self) -> int:
        """Расчёт lifetime балла"""
        monthly_wins = self.total_monthly_wins
        top10_count = len([a for a in self.awards if a.rank <= 10])

        return (
                self.words_learned +
                (monthly_wins * 1000) +
                (top10_count * 100) +
                (self.quizzes_passed * 2) +
                (self.best_streak_days * 10)
        )


class UserWord(Base):
    __tablename__ = "user_words"

    user_id = mapped_column(ForeignKey("users.id"), primary_key=True)
    word_id = mapped_column(ForeignKey("words.id"), primary_key=True)

    correct_streak = mapped_column(Integer, default=0, nullable=False)
    times_shown = mapped_column(Integer, default=0, nullable=False)
    times_correct = mapped_column(Integer, default=0, nullable=False)
    last_seen_at = mapped_column(DateTime, nullable=True)
    learned = mapped_column(Boolean, default=False, nullable=False)

    user = relationship("User", backref="learned_items")
    word = relationship("Word", backref="learned_by")


class PartOfSpeech(enum.Enum):
    """Части речи"""
    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adjective"
    ADVERB = "adverb"
    PHRASE = "phrase"
    PRONOUN = "pronoun"
    PREPOSITION = "preposition"
    CONJUNCTION = "conjunction"
    OTHER = "other"


class Word(Base):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    word_de: Mapped[str] = mapped_column(String(255), index=True)
    article: Mapped[Optional[str]] = mapped_column(String(10))

    pos: Mapped[PartOfSpeech] = mapped_column(SQLEnum(PartOfSpeech))
    level: Mapped[CEFRLevel] = mapped_column(SQLEnum(CEFRLevel), index=True)

    translation_ru: Mapped[Optional[str]] = mapped_column(String(255))
    translation_uk: Mapped[Optional[str]] = mapped_column(String(255))

    example_de: Mapped[Optional[str]] = mapped_column(Text)
    example_ru: Mapped[Optional[str]] = mapped_column(Text)
    example_uk: Mapped[Optional[str]] = mapped_column(Text)

    categories: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        default=list
    )

    times_shown: Mapped[int] = mapped_column(Integer, default=0)
    times_correct: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    quiz_questions: Mapped[List["QuizQuestion"]] = relationship(
        back_populates="word",
        cascade="all, delete-orphan"
    )

    @property
    def success_rate(self) -> float:
        if self.times_shown == 0:
            return 0.0
        return (self.times_correct / self.times_shown) * 100

    @property
    def full_word_de(self) -> str:
        if self.article and self.article != "-":
            return f"{self.article} {self.word_de}"
        return self.word_de

    def get_translation(self, language: str) -> Optional[str]:
        if language == "ru":
            return self.translation_ru
        elif language == "uk":
            return self.translation_uk
        return None

    def get_example(self, language: str) -> Optional[str]:
        if language == "de":
            return self.example_de
        elif language == "ru":
            return self.example_ru
        elif language == "uk":
            return self.example_uk
        return None


class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True)

    level: Mapped[CEFRLevel] = mapped_column(SQLEnum(CEFRLevel))
    translation_mode: Mapped[TranslationMode] = mapped_column(SQLEnum(TranslationMode))

    total_questions: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)

    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    user: Mapped["User"] = relationship(back_populates="quiz_sessions")
    questions: Mapped[List["QuizQuestion"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan"
    )

    @property
    def score_percentage(self) -> float:
        if self.total_questions == 0:
            return 0.0
        return (self.correct_answers / self.total_questions) * 100


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    session_id: Mapped[int] = mapped_column(ForeignKey("quiz_sessions.id", ondelete="CASCADE"), index=True)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id", ondelete="CASCADE"), index=True)

    user_answer: Mapped[Optional[str]] = mapped_column(String(255))
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean)

    answered_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["QuizSession"] = relationship(back_populates="questions")
    word: Mapped["Word"] = relationship(back_populates="quiz_questions")


# 🆕 НОВЫЕ МОДЕЛИ ДЛЯ МЕСЯЧНОЙ СИСТЕМЫ

class MonthlySeason(Base):
    """Месячный сезон рейтинга"""
    __tablename__ = "monthly_seasons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    winners_finalized: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    monthly_stats: Mapped[List["MonthlyStats"]] = relationship(
        back_populates="season",
        cascade="all, delete-orphan"
    )
    awards: Mapped[List["MonthlyAward"]] = relationship(
        back_populates="season",
        cascade="all, delete-orphan"
    )


class MonthlyStats(Base):
    """Статистика пользователя за месяц"""
    __tablename__ = "monthly_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    season_id: Mapped[int] = mapped_column(Integer, ForeignKey("monthly_seasons.id", ondelete="CASCADE"))

    monthly_streak: Mapped[int] = mapped_column(Integer, default=0)
    monthly_quizzes: Mapped[int] = mapped_column(Integer, default=0)
    monthly_words: Mapped[int] = mapped_column(Integer, default=0)
    monthly_reverse: Mapped[int] = mapped_column(Integer, default=0)
    monthly_avg_percent: Mapped[int] = mapped_column(Integer, default=0)
    # Для инкрементального расчёта среднего процента
    total_correct: Mapped[int] = mapped_column(Integer, default=0)
    total_questions: Mapped[int] = mapped_column(Integer, default=0)
    # Для инкрементального расчёта месячного стрика
    last_quiz_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    monthly_score: Mapped[int] = mapped_column(Integer, default=0)

    final_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="monthly_stats")
    season: Mapped["MonthlySeason"] = relationship(back_populates="monthly_stats")

    def calculate_monthly_score(self) -> int:
        """Расчёт месячного балла"""
        return (
                (self.monthly_streak * 15) +
                (self.monthly_quizzes * 8) +
                (self.monthly_words * 5) +
                (self.monthly_reverse * 5) +
                (self.monthly_avg_percent * 3)
        )




class MonthlyQuizEvent(Base):
    """Лог событий викторин для идемпотентного инкрементального апдейта"""
    __tablename__ = "monthly_quiz_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quiz_session_id: Mapped[int] = mapped_column(Integer, ForeignKey("quiz_sessions.id", ondelete="CASCADE"), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    season_id: Mapped[int] = mapped_column(Integer, ForeignKey("monthly_seasons.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class MonthlyAward(Base):
    """Награда за месяц"""
    __tablename__ = "monthly_awards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    season_id: Mapped[int] = mapped_column(Integer, ForeignKey("monthly_seasons.id", ondelete="CASCADE"))

    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    award_type: Mapped[str] = mapped_column(String(20), nullable=False)
    lifetime_bonus: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="awards")
    season: Mapped["MonthlySeason"] = relationship(back_populates="awards")

    @property
    def emoji(self) -> str:
        emoji_map = {
            'gold': '🥇',
            'silver': '🥈',
            'bronze': '🥉',
            'top10': '⭐'
        }
        return emoji_map.get(self.award_type, '🏆')


class WinStreak(Base):
    """Серии побед пользователя"""
    __tablename__ = "win_streaks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True)

    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    best_streak: Mapped[int] = mapped_column(Integer, default=0)
    total_wins: Mapped[int] = mapped_column(Integer, default=0)

    last_win_season: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("monthly_seasons.id", ondelete="SET NULL"),
        nullable=True
    )

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="win_streak")

    @property
    def streak_emoji(self) -> str:
        if self.current_streak >= 4:
            return '👑'
        elif self.current_streak == 3:
            return '🔥🔥'
        elif self.current_streak == 2:
            return '🔥'
        return ''

    @property
    def streak_title(self) -> str:
        if self.current_streak >= 4:
            return 'Легенда'
        elif self.current_streak == 3:
            return 'Трёхкратный чемпион'
        elif self.current_streak == 2:
            return 'Двукратный чемпион'
        return ''