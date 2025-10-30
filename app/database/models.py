from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import String, Integer, BigInteger, DateTime, Boolean, ForeignKey, Enum, Text, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Optional


class Base(DeclarativeBase):
    pass


class CEFRLevel(PyEnum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


class Article(PyEnum):
    DER = "der"
    DIE = "die"
    DAS = "das"
    NONE = "-"


class PartOfSpeech(PyEnum):
    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adj"
    ADVERB = "adv"
    OTHER = "other"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    selected_level: Mapped[Optional[str]] = mapped_column(Enum(CEFRLevel), nullable=True)
    translation_mode: Mapped[str] = mapped_column(String(10), default="DE-RU", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    sessions: Mapped[list["Session"]] = relationship(back_populates="user")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    title_ru: Mapped[str] = mapped_column(String(255), nullable=False)
    title_de: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    word_categories: Mapped[list["WordCategory"]] = relationship(back_populates="category")


class MasterWord(Base):
    __tablename__ = "master_words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lemma: Mapped[str] = mapped_column(String(255), nullable=False)
    article: Mapped[Optional[str]] = mapped_column(Enum(Article), nullable=True)
    pos: Mapped[str] = mapped_column(Enum(PartOfSpeech), nullable=False)
    cefr: Mapped[str] = mapped_column(Enum(CEFRLevel), nullable=False)
    translation_ru: Mapped[str] = mapped_column(String(500), nullable=False)
    example_de: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    example_ru: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    plural: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    separable_prefix: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    word_categories: Mapped[list["WordCategory"]] = relationship(back_populates="word")
    session_items: Mapped[list["SessionItem"]] = relationship(back_populates="word")


class WordCategory(Base):
    __tablename__ = "word_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    word_id: Mapped[int] = mapped_column(Integer, ForeignKey("master_words.id"), nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id"), nullable=False)
    weight: Mapped[int] = mapped_column(Integer, default=1)

    word: Mapped["MasterWord"] = relationship(back_populates="word_categories")
    category: Mapped["Category"] = relationship(back_populates="word_categories")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    level: Mapped[str] = mapped_column(Enum(CEFRLevel), nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="sessions")
    items: Mapped[list["SessionItem"]] = relationship(back_populates="session")


class SessionItem(Base):
    __tablename__ = "session_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id"), nullable=False)
    word_id: Mapped[int] = mapped_column(Integer, ForeignKey("master_words.id"), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    answered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["Session"] = relationship(back_populates="items")
    word: Mapped["MasterWord"] = relationship(back_populates="session_items")