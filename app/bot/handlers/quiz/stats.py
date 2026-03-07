"""
Статистика и прогресс пользователя — ПОЛНАЯ ЛОКАЛИЗАЦИЯ
"""

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import logging

logger = logging.getLogger(__name__)

from app.bot.utils import delete_messages_fast, ensure_anchor
from app.database.models import User, QuizSession
from app.locales import get_text
from app.services.quiz_service import (
    get_user_progress_stats,
    get_user_progress_stats_all_levels,
)

router = Router()

MODE_DICT = {
    "DE_TO_RU": "🇩🇪 → 🏴", "RU_TO_DE": "🏴 → 🇩🇪",
    "DE_TO_UK": "🇩🇪 → 🇺🇦", "UK_TO_DE": "🇺🇦 → 🇩🇪",
    "DE_TO_EN": "🇩🇪 → 🇬🇧", "EN_TO_DE": "🇬🇧 → 🇩🇪",
    "DE_TO_TR": "🇩🇪 → 🇹🇷", "TR_TO_DE": "🇹🇷 → 🇩🇪",
}

def get_stats_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=get_text("stats_btn_rating", lang),
                callback_data="show_my_rating"
            )]
        ]
    )


def create_progress_bar(current: int, total: int, length: int = 10) -> str:
    if total == 0:
        return "░" * length + " 0%"
    percentage = min(100, int((current / total) * 100))
    filled = int((current / total) * length)
    empty = length - filled
    return f"{'▓' * filled}{'░' * empty} {percentage}%"


def get_achievement_emoji(percentage: float) -> str:
    if percentage >= 95: return "🏆"
    elif percentage >= 85: return "🥇"
    elif percentage >= 75: return "🥈"
    elif percentage >= 60: return "🥉"
    return "📝"


@router.message(Command("stats"))
@router.message(F.text.in_(["📊 Статистика", "📊 Статистика", "📊 Statistics", "📊 İstatistik"]))
async def show_statistics(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    user = await session.get(User, user_id)

    try:
        await message.delete()
    except:
        pass

    if not user or not user.level:
        lang = user.interface_language if user else "ru"
        await message.answer(get_text("stats_no_level", lang))
        return

    lang = user.interface_language or "ru"

    # Данные
    try:
        overall_progress = await get_user_progress_stats_all_levels(user_id, session)
    except:
        overall_progress = {'total_words': 0, 'seen_words': 0, 'learned_words': 0, 'struggling_words': 0, 'new_words': 0}

    try:
        progress = await get_user_progress_stats(user_id, user.level, session)
    except:
        progress = {'total_words': 0, 'seen_words': 0, 'learned_words': 0, 'struggling_words': 0, 'new_words': 0}

    result = await session.execute(
        select(QuizSession).where(
            QuizSession.user_id == user_id,
            QuizSession.level == user.level,
            QuizSession.completed_at.isnot(None)
        ).order_by(QuizSession.started_at.desc())
    )
    all_level_sessions = result.scalars().all()

    # ========================================================================
    # ФОРМИРУЕМ ТЕКСТ
    # ========================================================================

    mode = MODE_DICT.get(user.translation_mode.value, "🇩🇪 → 🏴")
    total = progress['total_words']
    learned = progress['learned_words']
    in_progress = progress['seen_words'] - learned
    new = progress['new_words']
    difficult = progress['struggling_words']
    overall_learned = overall_progress['learned_words']
    overall_total = overall_progress['total_words']

    text = get_text("stats_header", lang) + "\n\n"

    # Уровень + прогресс-бар
    bar = create_progress_bar(learned, total, length=12)
    text += f"🎯 <b>{user.level.value}</b> · {mode}\n"
    text += f"{bar}\n"
    text += get_text("stats_learned_of", lang, learned=learned, total=total) + "\n\n"

    # Детализация
    text += get_text("stats_details", lang, progress=in_progress, new=new, difficult=difficult) + "\n\n"

    # Достижения
    if overall_learned >= 500: emoji = "🏆"
    elif overall_learned >= 200: emoji = "🥇"
    elif overall_learned >= 100: emoji = "🥈"
    elif overall_learned >= 50: emoji = "🥉"
    else: emoji = "⭐"

    text += f"{emoji} {get_text('stats_achievements_title', lang)}\n"
    text += get_text("stats_words_count", lang, count=overall_learned) + "\n"
    text += get_text("stats_streak_line", lang, days=user.streak_days) + "\n\n"

    # Викторины
    if all_level_sessions:
        total_quizzes = len(all_level_sessions)
        total_questions = sum(s.total_questions for s in all_level_sessions)
        total_correct = sum(s.correct_answers for s in all_level_sessions)
        avg_percent = (total_correct / total_questions * 100) if total_questions > 0 else 0
        best_result = max((s.correct_answers / s.total_questions * 100) for s in all_level_sessions)

        q_emoji = get_achievement_emoji(avg_percent)
        text += f"{q_emoji} {get_text('stats_quizzes_header', lang, level=user.level.value)}\n"
        text += get_text("stats_quizzes_passed_line", lang, count=total_quizzes) + "\n"
        text += get_text("stats_quizzes_avg_line", lang, percent=f"{avg_percent:.0f}") + "\n"
        text += get_text("stats_quizzes_best_line", lang, percent=f"{best_result:.0f}") + "\n\n"
    else:
        text += f"📝 {get_text('stats_quizzes_header', lang, level=user.level.value)}\n"
        text += get_text("stats_quizzes_empty", lang) + "\n\n"

    # Последние викторины
    if all_level_sessions:
        text += get_text("stats_recent_header", lang) + "\n"
        for s in all_level_sessions[:3]:
            pct = (s.correct_answers / s.total_questions * 100) if s.total_questions > 0 else 0
            date_str = s.started_at.strftime("%d.%m")
            e = get_achievement_emoji(pct)
            text += f"{e} {date_str} — {s.correct_answers}/{s.total_questions} ({pct:.0f}%)\n"
        text += "\n"

    # Общий прогресс
    if overall_total > 0:
        overall_bar = create_progress_bar(overall_learned, overall_total, length=12)
        text += get_text("stats_overall_header", lang) + "\n"
        text += f"{overall_bar}\n"
        text += get_text("stats_overall_learned", lang, learned=overall_learned, total=overall_total) + "\n\n"

    # Мотивация
    if learned == 0:
        text += get_text("stats_cta_start", lang)
    elif learned < total * 0.3:
        text += get_text("stats_cta_begin", lang)
    elif learned < total * 0.7:
        text += get_text("stats_cta_halfway", lang)
    else:
        text += get_text("stats_cta_almost", lang)

    text += "\n\n"
    text += get_text("stats_explanation", lang)

    # Якорь + отправка
    old_anchor_id, new_anchor_id = await ensure_anchor(message, session, user, emoji="📊")
    if old_anchor_id:
        await delete_messages_fast(message.bot, message.chat.id, old_anchor_id, message.message_id)

    await message.answer(text, reply_markup=get_stats_keyboard(lang))