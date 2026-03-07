from datetime import datetime, date
from sqlalchemy import Date
from typing import List, Optional

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

    # Старые поля для статистики
    last_active_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    words_learned: Mapped[int] = mapped_column(Integer, default=0)
    quizzes_passed: Mapped[int] = mapped_column(Integer, default=0)
    success_rate: Mapped[int] = mapped_column(Integer, default=0)

    # Новые поля и настройки
    level: Mapped[CEFRLevel] = mapped_column(SQLEnum(CEFRLevel), default=CEFRLevel.A1)
    translation_mode: Mapped[TranslationMode] = mapped_column(SQLEnum(TranslationMode),
                                                              default=TranslationMode.DE_TO_RU)
    interface_language: Mapped[str] = mapped_column(String(2), default="ru")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    anchor_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    # === ЯЗЫКИ И ЛОКАЛИЗАЦИЯ ===
    telegram_language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # === TIMEZONE ===
    timezone: Mapped[str] = mapped_column(String(50), default="Europe/Berlin")
    utc_offset: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # === ВРЕМЯ АКТИВНОСТИ ===
    first_quiz_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_quiz_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # === НАПОМИНАНИЯ ===
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    notification_time: Mapped[str] = mapped_column(String(5), default="20:00")
    notification_days: Mapped[List[int]] = mapped_column(ARRAY(Integer), default=[0, 1, 2, 3, 4, 5, 6])
    last_notification_sent: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # === НАСТРОЙКИ ВИКТОРИНЫ ===
    quiz_word_count: Mapped[int] = mapped_column(Integer, default=25)

    # === МЕСЯЧНАЯ СИСТЕМА РЕЙТИНГА ===
    lifetime_score: Mapped[int] = mapped_column(Integer, default=0)
    best_streak_days: Mapped[int] = mapped_column(Integer, default=0)
    total_monthly_wins: Mapped[int] = mapped_column(Integer, default=0)

    # Связи
    quiz_sessions: Mapped[List["QuizSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    @property
    def display_name(self) -> str:
        """Отображаемое имя: приоритет имя+фамилия"""
        if self.first_name:
            name = self.first_name
            if self.last_name:
                name += f" {self.last_name}"
            return name
        elif self.last_name:
            return self.last_name
        elif self.username:
            return self.username
        else:
            return f"User {self.id}"

class UserWord(Base):
    __tablename__ = "user_words"

    user_id = mapped_column(ForeignKey("users.id"), primary_key=True)
    word_id = mapped_column(ForeignKey("words.id"), primary_key=True)

    # прогресс по слову
    correct_streak = mapped_column(Integer, default=0, nullable=False)
    times_shown = mapped_column(Integer, default=0, nullable=False)
    times_correct = mapped_column(Integer, default=0, nullable=False)
    last_seen_at = mapped_column(DateTime, nullable=True)

    # считается "выучено", когда достигнут порог streak
    learned = mapped_column(Boolean, default=False, nullable=False)

    created_at = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

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

    # Немецкое слово
    word_de: Mapped[str] = mapped_column(String(255), index=True)
    article: Mapped[Optional[str]] = mapped_column(String(10))  # der/die/das

    # Часть речи и уровень
    pos: Mapped[PartOfSpeech] = mapped_column(SQLEnum(PartOfSpeech))
    level: Mapped[CEFRLevel] = mapped_column(SQLEnum(CEFRLevel), index=True)

    # Переводы
    translation_ru: Mapped[Optional[str]] = mapped_column(String(255))
    translation_uk: Mapped[Optional[str]] = mapped_column(String(255))

    # Примеры использования
    example_de: Mapped[Optional[str]] = mapped_column(Text)
    example_ru: Mapped[Optional[str]] = mapped_column(Text)
    example_uk: Mapped[Optional[str]] = mapped_column(Text)

    # Категории (массив строк)
    categories: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        default=list
    )

    # Статистика
    times_shown: Mapped[int] = mapped_column(Integer, default=0)
    times_correct: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    # Relationships
    quiz_questions: Mapped[List["QuizQuestion"]] = relationship(
        back_populates="word",
        cascade="all, delete-orphan"
    )

    @property
    def success_rate(self) -> float:
        """Процент правильных ответов"""
        if self.times_shown == 0:
            return 0.0
        return (self.times_correct / self.times_shown) * 100

    @property
    def full_word_de(self) -> str:
        """Полное немецкое слово с артиклем"""
        if self.article and self.article != "-":
            return f"{self.article} {self.word_de}"
        return self.word_de

    def get_translation(self, language: str) -> Optional[str]:
        """Получить перевод на указанный язык"""
        if language == "ru":
            return self.translation_ru
        elif language == "uk":
            return self.translation_uk
        return None

    def get_example(self, language: str) -> Optional[str]:
        """Получить пример на указанном языке"""
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
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )

    level: Mapped[CEFRLevel] = mapped_column(SQLEnum(CEFRLevel))
    translation_mode: Mapped[TranslationMode] = mapped_column(
        SQLEnum(TranslationMode)
    )

    # Статистика сессии
    total_questions: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)

    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="quiz_sessions")
    questions: Mapped[List["QuizQuestion"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan"
    )

    @property
    def score_percentage(self) -> float:
        """Процент правильных ответов"""
        if self.total_questions == 0:
            return 0.0
        return (self.correct_answers / self.total_questions) * 100


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    session_id: Mapped[int] = mapped_column(
        ForeignKey("quiz_sessions.id", ondelete="CASCADE"),
        index=True
    )
    word_id: Mapped[int] = mapped_column(
        ForeignKey("words.id", ondelete="CASCADE"),
        index=True
    )

    # Ответ пользователя
    user_answer: Mapped[Optional[str]] = mapped_column(String(255))
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean)

    # Время ответа
    answered_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    # Relationships
    session: Mapped["QuizSession"] = relationship(back_populates="questions")
    word: Mapped["Word"] = relationship(back_populates="quiz_questions")


# ============================================================================
# МЕСЯЧНЫЙ РЕЙТИНГ
# ============================================================================

class MonthlySeason(Base):
    """Месячный сезон соревнований"""
    __tablename__ = "monthly_seasons"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    winners_finalized: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    stats: Mapped[List["MonthlyStats"]] = relationship(back_populates="season", cascade="all, delete-orphan")
    awards: Mapped[List["MonthlyAward"]] = relationship(back_populates="season", cascade="all, delete-orphan")


class MonthlyStats(Base):
    """Статистика пользователя за месяц"""
    __tablename__ = "monthly_stats"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    season_id: Mapped[int] = mapped_column(ForeignKey("monthly_seasons.id", ondelete="CASCADE"), nullable=False)

    # Основные метрики
    monthly_score: Mapped[int] = mapped_column(Integer, default=0)
    monthly_quizzes: Mapped[int] = mapped_column(Integer, default=0)
    monthly_reverse: Mapped[int] = mapped_column(Integer, default=0)
    monthly_words: Mapped[int] = mapped_column(Integer, default=0)
    monthly_streak: Mapped[int] = mapped_column(Integer, default=0)
    monthly_avg_percent: Mapped[int] = mapped_column(Integer, default=0)

    # Для расчёта среднего
    total_correct: Mapped[int] = mapped_column(Integer, default=0)
    total_questions: Mapped[int] = mapped_column(Integer, default=0)

    # Финальный ранг (заполняется в конце месяца)
    final_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Служебные
    last_quiz_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship(backref="monthly_stats")
    season: Mapped["MonthlySeason"] = relationship(back_populates="stats")

    def calculate_monthly_score(self) -> int:
        """Рассчитать месячный балл по формуле"""
        score = 0
        score += self.monthly_quizzes * 10
        score += self.monthly_reverse * 5
        score += self.monthly_words * 2
        score += self.monthly_streak * 3

        # Бонус за средний процент
        if self.monthly_avg_percent >= 90:
            score += 50
        elif self.monthly_avg_percent >= 80:
            score += 30
        elif self.monthly_avg_percent >= 70:
            score += 15

        return score


class MonthlyQuizEvent(Base):
    """Таблица для идемпотентности - какие викторины уже учтены"""
    __tablename__ = "monthly_quiz_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    quiz_session_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    season_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WinStreak(Base):
    """Серия побед пользователя (win streak)"""
    __tablename__ = "win_streaks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True,
                                         nullable=False)

    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    best_streak: Mapped[int] = mapped_column(Integer, default=0)
    total_wins: Mapped[int] = mapped_column(Integer, default=0)
    last_win_season: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user: Mapped["User"] = relationship(backref="win_streak")

    @property
    def streak_emoji(self) -> str:
        """Эмодзи в зависимости от текущего стрика"""
        if self.current_streak >= 12:
            return "👑"
        elif self.current_streak >= 6:
            return "🔥🔥🔥"
        elif self.current_streak >= 3:
            return "🔥🔥"
        elif self.current_streak >= 1:
            return "🔥"
        return ""

    @property
    def streak_title(self) -> str:
        """Титул в зависимости от стрика"""
        if self.current_streak >= 12:
            return "Легенда"
        elif self.current_streak >= 6:
            return "Доминатор"
        elif self.current_streak >= 3:
            return "Чемпион"
        return ""


class MonthlyAward(Base):
    """Награды за месячные достижения"""
    __tablename__ = "monthly_awards"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    season_id: Mapped[int] = mapped_column(ForeignKey("monthly_seasons.id", ondelete="CASCADE"), nullable=False)

    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    award_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "gold", "silver", "bronze", "top10"
    lifetime_bonus: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship(backref="monthly_awards")
    season: Mapped["MonthlySeason"] = relationship(back_populates="awards")