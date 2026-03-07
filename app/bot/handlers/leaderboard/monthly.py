"""
Мой рейтинг — вкладка «Месяц»
Персональная карточка за текущий месяц
"""

import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

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
        print(f"   ❌ Ошибка создания якоря: {e}")
        return old_anchor_id, None


def get_rating_keyboard(lang: str, current_tab: str = "monthly") -> InlineKeyboardMarkup:
    """Клавиатура Мой рейтинг: вкладки + кнопка таблицы"""
    texts = get_leaderboard_keyboard_text(lang, current_tab)

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=texts['monthly'], callback_data="rating_monthly"),
                InlineKeyboardButton(text=texts['alltime'], callback_data="rating_alltime")
            ],
            [
                InlineKeyboardButton(
                    text="📊 Таблица лидеров" if lang == "ru"
                    else "📊 Таблиця лідерів" if lang == "uk"
                    else "📊 Leaderboard" if lang == "en"
                    else "📊 Liderlik Tablosu",
                    callback_data="leaderboard_table_monthly"
                )
            ]
        ]
    )


def build_monthly_card(
    user: User,
    user_rank: dict,
    season,
    lang: str
) -> str:
    """
    Персональная карточка за месяц.
    Все данные берутся из user_rank (напрямую из MonthlyStats),
    НЕ из leaderboard — работает для любой позиции.
    """

    month_name = format_month_name(season.month, lang)

    # ═══════════════ ЗАГОЛОВОК ═══════════════
    text = f"🏆 <b>Мой рейтинг — {month_name} {season.year}</b>\n\n"

    if not user_rank:
        text += "📍 Ты ещё не в рейтинге\n"
        text += "🚀 Пройди первую викторину!\n"
        return text

    rank = user_rank['rank']
    score = user_rank['monthly_score']
    total_users = user_rank.get('total_users', 1)

    # Данные напрямую из MonthlyStats (FIX: не зависит от limit leaderboard)
    quizzes = user_rank.get('monthly_quizzes', 0)
    words = user_rank.get('monthly_words', 0)
    streak = user_rank.get('monthly_streak', 0)
    avg_pct = user_rank.get('monthly_avg_percent', 0)

    # ═══════════════ ПОЗИЦИЯ ═══════════════
    text += f"📍 Позиция: <b>#{rank}</b> из {total_users}\n"
    text += f"💎 Баллы: <b>{score}</b>\n\n"

    # ═══════════════ ДЕТАЛИ МЕСЯЦА ═══════════════
    text += f"⭐ <b>Твой {month_name}:</b>\n"
    text += f"├ Викторин: {quizzes}\n"
    text += f"├ Выучено слов: {words}\n"
    text += f"├ Стрик: {streak} дн.\n"
    text += f"└ Средний результат: {avg_pct}%\n"

    # ═══════════════ ПОДСКАЗКА ═══════════════
    text += "\n━━━━━━━━━━━━━━━━━\n"
    text += "💡 <b>Как заработать баллы:</b>\n"
    text += "• Пройденная викторина → +10\n"
    text += "• Режим «Реверс» → +5\n"
    text += "• Выученное слово → +2\n"
    text += "• День подряд → +3\n"
    text += "• Точность 90%+ → +50 бонус\n"

    return text


# ============================================================================
# ТОЧКА ВХОДА: кнопка 🏆 Мой рейтинг из статистики
# ============================================================================

@router.callback_query(F.data == "show_my_rating")
async def show_my_rating_callback(callback: CallbackQuery, session: AsyncSession):
    """Кнопка 'Мой рейтинг' из статистики"""
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language if user else "ru"
    season = await get_current_season(session)

    if not season:
        await callback.message.edit_text("❌ Рейтинг пока не активен.")
        return

    user_rank = await get_user_monthly_rank(user.id, session, season_id=season.id)
    text = build_monthly_card(user, user_rank, season, lang)

    try:
        await callback.message.edit_text(text, reply_markup=get_rating_keyboard(lang, "monthly"))
    except Exception:
        await callback.message.answer(text, reply_markup=get_rating_keyboard(lang, "monthly"))


# ============================================================================
# ТОЧКА ВХОДА: команда /leaderboard или кнопка 🏆 Рейтинг
# ============================================================================

@router.message(Command("leaderboard"))
@router.message(F.text.in_(["🏆 Рейтинг", "🏆 Рейтинг"]))
async def show_leaderboard(message: Message, session: AsyncSession):
    """Кнопка/команда — показывает месячную карточку"""
    user = await session.get(User, message.from_user.id)

    try:
        await message.delete()
    except:
        pass

    lang = user.interface_language if user else "ru"
    season = await get_current_season(session)

    if not season:
        await message.answer("❌ Рейтинг пока не активен.")
        return

    user_rank = await get_user_monthly_rank(user.id, session, season_id=season.id)
    text = build_monthly_card(user, user_rank, season, lang)

    old_anchor_id, new_anchor_id = await ensure_anchor(message, session, user, emoji="🏆")
    if old_anchor_id:
        await delete_messages_fast(message.bot, message.chat.id, old_anchor_id, message.message_id)

    await message.answer(text, reply_markup=get_rating_keyboard(lang, "monthly"))


# ============================================================================
# ПЕРЕКЛЮЧЕНИЕ ВКЛАДКИ: Месяц
# ============================================================================

@router.callback_query(F.data == "rating_monthly")
async def switch_to_monthly(callback: CallbackQuery, session: AsyncSession):
    """Вкладка Месяц — edit текущего сообщения"""
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language if user else "ru"
    season = await get_current_season(session)

    if not season:
        await callback.message.edit_text("❌ Рейтинг не активен")
        return

    user_rank = await get_user_monthly_rank(user.id, session, season_id=season.id)
    text = build_monthly_card(user, user_rank, season, lang)

    await callback.message.edit_text(text, reply_markup=get_rating_keyboard(lang, "monthly"))