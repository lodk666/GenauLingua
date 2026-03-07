"""
Мой рейтинг — вкладка «Месяц»
Персональная карточка за текущий месяц — ЛОКАЛИЗОВАНО
"""

import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

import logging

logger = logging.getLogger(__name__)

from app.database.models import User
from app.bot.keyboards import get_main_menu_keyboard
from app.services.monthly_leaderboard_service import (
    get_monthly_leaderboard,
    get_user_monthly_rank,
    get_current_season
)
from app.bot.handlers.leaderboard.utils import (
    format_month_name,
    create_progress_bar,
    get_leaderboard_keyboard_text
)
from app.locales import get_text

router = Router()


async def delete_messages_fast(bot, chat_id: int, start_id: int, end_id: int):
    tasks = []
    for msg_id in range(start_id, end_id):
        tasks.append(bot.delete_message(chat_id=chat_id, message_id=msg_id))
    results = await asyncio.gather(*tasks, return_exceptions=True)


async def ensure_anchor(message: Message, session: AsyncSession, user: User, emoji: str = "🏆"):
    old_anchor_id = user.anchor_message_id
    lang = user.interface_language or "ru"
    try:
        sent = await message.answer(emoji, reply_markup=get_main_menu_keyboard(lang))
        new_anchor_id = sent.message_id
        user.anchor_message_id = new_anchor_id
        await session.commit()
        return old_anchor_id, new_anchor_id
    except Exception as e:
        logger.error(f"Ошибка создания якоря: {e}")
        return old_anchor_id, None


def get_rating_keyboard(lang: str, current_tab: str = "monthly") -> InlineKeyboardMarkup:
    texts = get_leaderboard_keyboard_text(lang, current_tab)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=texts['monthly'], callback_data="rating_monthly"),
                InlineKeyboardButton(text=texts['alltime'], callback_data="rating_alltime")
            ],
            [
                InlineKeyboardButton(
                    text=get_text("btn_leaderboard_table", lang),
                    callback_data="leaderboard_table_monthly"
                )
            ]
        ]
    )


def build_monthly_card(user: User, user_rank: dict, season, lang: str) -> str:
    month_name = format_month_name(season.month, lang)

    text = get_text("rating_title_monthly", lang, month=month_name, year=season.year) + "\n\n"

    if not user_rank:
        text += get_text("rating_not_in_ranking", lang) + "\n"
        text += get_text("rating_start_quiz", lang) + "\n"
        return text

    rank = user_rank['rank']
    score = user_rank['monthly_score']
    total_users = user_rank.get('total_users', 1)
    quizzes = user_rank.get('monthly_quizzes', 0)
    words = user_rank.get('monthly_words', 0)
    streak = user_rank.get('monthly_streak', 0)
    avg_pct = user_rank.get('monthly_avg_percent', 0)

    text += get_text("rating_position", lang, rank=rank, total=total_users) + "\n"
    text += get_text("rating_points", lang, score=score) + "\n\n"

    text += get_text("rating_your_month", lang, month=month_name) + "\n"
    text += get_text("rating_quizzes", lang, count=quizzes) + "\n"
    text += get_text("rating_words_learned", lang, count=words) + "\n"
    text += get_text("rating_streak", lang, count=streak) + "\n"
    text += get_text("rating_avg_result", lang, percent=avg_pct) + "\n"

    text += "\n━━━━━━━━━━━━━━━━━\n"
    text += get_text("rating_scoring_title", lang) + "\n"
    text += get_text("rating_scoring_quiz", lang) + "\n"
    text += get_text("rating_scoring_reverse", lang) + "\n"
    text += get_text("rating_scoring_word", lang) + "\n"
    text += get_text("rating_scoring_streak", lang) + "\n"
    text += get_text("rating_scoring_bonus", lang) + "\n"

    return text


@router.callback_query(F.data == "show_my_rating")
async def show_my_rating_callback(callback: CallbackQuery, session: AsyncSession):
    await callback.answer()
    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language if user else "ru"
    season = await get_current_season(session)

    if not season:
        await callback.message.edit_text(get_text("rating_not_active", lang))
        return

    user_rank = await get_user_monthly_rank(user.id, session, season_id=season.id)
    text = build_monthly_card(user, user_rank, season, lang)

    try:
        await callback.message.edit_text(text, reply_markup=get_rating_keyboard(lang, "monthly"))
    except Exception:
        await callback.message.answer(text, reply_markup=get_rating_keyboard(lang, "monthly"))


@router.message(Command("leaderboard"))
@router.message(F.text.in_(["🏆 Рейтинг", "🏆 Рейтинг"]))
async def show_leaderboard(message: Message, session: AsyncSession):
    user = await session.get(User, message.from_user.id)
    try:
        await message.delete()
    except:
        pass

    lang = user.interface_language if user else "ru"
    season = await get_current_season(session)

    if not season:
        await message.answer(get_text("rating_not_active", lang))
        return

    user_rank = await get_user_monthly_rank(user.id, session, season_id=season.id)
    text = build_monthly_card(user, user_rank, season, lang)

    old_anchor_id, new_anchor_id = await ensure_anchor(message, session, user, emoji="🏆")
    if old_anchor_id:
        await delete_messages_fast(message.bot, message.chat.id, old_anchor_id, message.message_id)

    await message.answer(text, reply_markup=get_rating_keyboard(lang, "monthly"))


@router.callback_query(F.data == "rating_monthly")
async def switch_to_monthly(callback: CallbackQuery, session: AsyncSession):
    await callback.answer()
    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language if user else "ru"
    season = await get_current_season(session)

    if not season:
        await callback.message.edit_text(get_text("rating_not_active", lang))
        return

    user_rank = await get_user_monthly_rank(user.id, session, season_id=season.id)
    text = build_monthly_card(user, user_rank, season, lang)
    await callback.message.edit_text(text, reply_markup=get_rating_keyboard(lang, "monthly"))