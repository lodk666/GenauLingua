from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    BigInteger, String, Boolean, DateTime, Integer, 
    ForeignKey, Text, Enum as SQLEnum, Float
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY
import enum


class Base(DeclarativeBase):
    pass


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


class CEFRLevel(enum.Enum):
    """Уровни по CEFR"""
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


class TranslationMode(enum.Enum):
    """Режимы перевода"""
    DE_TO_RU = "de_to_ru"  # Немецкий → Русский
    RU_TO_DE = "ru_to_de"  # Русский → Немецкий
    DE_TO_UK = "de_to_uk"  # Немецкий → Украинский
    UK_TO_DE = "uk_to_de"  # Украинский → Немецкий


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(255))
    first_name: Mapped[Optional[str]] = mapped_column(String(255))
    last_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Настройки пользователя
    level: Mapped[CEFRLevel] = mapped_column(
        SQLEnum(CEFRLevel), 
        default=CEFRLevel.A1
    )
    translation_mode: Mapped[TranslationMode] = mapped_column(
        SQLEnum(TranslationMode), 
        default=TranslationMode.DE_TO_RU
    )
    
    # Язык интерфейса (ru/uk)
    interface_language: Mapped[str] = mapped_column(String(2), default="ru")
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow
    )
    
    # Relationships
    quiz_sessions: Mapped[List["QuizSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )


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
