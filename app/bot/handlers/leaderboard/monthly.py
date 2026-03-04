"""
Месячный рейтинг
Отображает топ-10 игроков текущего месяца
УЛУЧШЕННАЯ ВЕРСИЯ — понятная, красивая, интересная
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
    format_user_card,
    format_month_name,
    create_progress_bar,
    get_leaderboard_keyboard_text,
    get_localized_text
)

router = Router()


async def delete_messages_fast(bot, chat_id: int, start_id: int, end_id: int):
    """Быстрое удаление сообщений между якорями"""
    tasks = []
    for msg_id in range(start_id, end_id):
        tasks.append(bot.delete_message(chat_id=chat_id, message_id=msg_id))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    deleted = sum(1 for r in results if not isinstance(r, Exception))
    print(f"   🧹 Удалено {deleted}/{len(tasks)} сообщений")


async def ensure_anchor(message: Message, session: AsyncSession, user: User, emoji: str = "🏆"):
    """Создание нового якоря"""
    old_anchor_id = user.anchor_message_id
    lang = user.interface_language or "ru"
    try:
        sent = await message.answer(emoji, reply_markup=get_main_menu_keyboard(lang))
        new_anchor_id = sent.message_id
        user.anchor_message_id = new_anchor_id
        await session.commit()
        print(f"   ✨ Создан новый якорь {new_anchor_id}")
        return old_anchor_id, new_anchor_id
    except Exception as e:
        print(f"   ❌ Ошибка создания якоря: {e}")
        return old_anchor_id, None


def get_leaderboard_keyboard(lang: str, current_tab: str = "monthly") -> InlineKeyboardMarkup:
    """Клавиатура переключения между вкладками рейтинга"""
    texts = get_leaderboard_keyboard_text(lang, current_tab)

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=texts['monthly'], callback_data="leaderboard_monthly"),
                InlineKeyboardButton(text=texts['alltime'], callback_data="leaderboard_alltime")
            ]
        ]
    )


def format_monthly_leaderboard(
    leaderboard: list,
    user_rank: dict,
    season,
    user_id: int,
    lang: str
) -> str:
    """
    Форматировать текст месячного рейтинга — УЛУЧШЕННАЯ ВЕРСИЯ

    Args:
        leaderboard: список топ-10
        user_rank: данные текущего пользователя
        season: текущий сезон
        user_id: ID текущего пользователя
        lang: язык интерфейса

    Returns:
        Готовый текст для отправки
    """
    month_name = format_month_name(season.month, lang)

    # Заголовок
    title_template = get_localized_text("title_monthly", lang)
    text = f"<b>{title_template.format(month=month_name, year=season.year)}</b>\n\n"

    # Топ-10 (или пусто)
    if not leaderboard:
        text += get_localized_text("no_participants", lang)
    else:
        for entry in leaderboard:
            rank = entry["rank"]
            is_current_user = (entry["user_id"] == user_id)

            card = format_user_card(entry, rank, is_current_user, lang)
            text += f"{card}\n"

    # Информация о текущем пользователе
    if user_rank:
        rank = user_rank['rank']
        score = user_rank['monthly_score']
        total_users = user_rank.get('total_users', 1)

        text += "\n" + "━" * 17 + "\n"

        # Позиция
        position_text = get_localized_text("your_position", lang).format(rank=rank)
        text += f"{position_text}\n"

        # Баллы
        points_text = get_localized_text("points", lang).format(score=score)
        text += f"{points_text}\n"

        # X из Y участников (вместо Топ X%)
        text += f"📊 {rank} из {total_users}\n\n"

        # Прогресс-бар до топ-3 (если не в топ-3)
        if rank > 3 and leaderboard and len(leaderboard) >= 3:
            top3_score = leaderboard[2]["monthly_score"]  # Баллы 3-го места
            diff = top3_score - score + 1

            if diff > 0:
                progress_bar = create_progress_bar(score, top3_score, length=10)

                text += f"🎯 До топ-3:\n"
                text += f"{progress_bar} ({diff} баллов)\n\n"
    else:
        text += "\n"
        text += get_localized_text("no_participation", lang)

    # Формула начисления баллов — КОРОТКИЙ ВАРИАНТ
    text += "━" * 17 + "\n"

    if lang in ["ru", "uk"]:
        text += "💡 <b>Как зарабоют баллы:</b>\n"
        text += "• Викторина → 10 баллов\n"
        text += "• Реверс → +5 бонус\n"
        text += "• Слово выучено → +2 балла\n"
        text += "• День подряд → +3 балла\n"
        text += "• 90%+ правильных → +50 бонус\n"
        text += "• 80%+ правильных → +30 бонус\n"
    else:
        text += "💡 <b>How to earn points:</b>\n"
        text += "• Quiz → 10 points\n"
        text += "• Reverse → +5 bonus\n"
        text += "• Word learned → +2 points\n"
        text += "• Day streak → +3 points\n"
        text += "• 90%+ correct → +50 bonus\n"
        text += "• 80%+ correct → +30 bonus\n"

    return text


# ============================================================================
# КОМАНДА /leaderboard И КНОПКА 🏆 РЕЙТИНГ
# ============================================================================

@router.message(Command("leaderboard"))
@router.message(F.text.in_(["🏆 Рейтинг", "🏆 Рейтинг"]))
async def show_leaderboard(message: Message, session: AsyncSession):
    """Показать месячный рейтинг (команда или кнопка)"""
    user_id = message.from_user.id
    user = await session.get(User, user_id)

    try:
        await message.delete()
    except:
        pass

    lang = user.interface_language if user else "ru"

    # Получаем данные
    season = await get_current_season(session)

    if not season:
        no_season_text = {
            "ru": "❌ Месячный рейтинг пока не активен.",
            "uk": "❌ Місячний рейтинг поки не активний.",
            "en": "❌ Monthly leaderboard is not active yet.",
            "tr": "❌ Aylık sıralama henüz aktif değil."
        }
        await message.answer(no_season_text.get(lang, no_season_text["ru"]))
        return

    leaderboard = await get_monthly_leaderboard(session, season_id=season.id, limit=10)
    user_rank = await get_user_monthly_rank(user.id, session, season_id=season.id)

    # Формируем текст
    text = format_monthly_leaderboard(leaderboard, user_rank, season, user.id, lang)

    # Создаём якорь и очищаем старое
    old_anchor_id, new_anchor_id = await ensure_anchor(message, session, user, emoji="🏆")

    if old_anchor_id:
        current_msg_id = message.message_id
        await delete_messages_fast(message.bot, message.chat.id, old_anchor_id, current_msg_id)

    # Отправляем рейтинг
    await message.answer(
        text,
        reply_markup=get_leaderboard_keyboard(lang, current_tab="monthly")
    )


# ============================================================================
# CALLBACK ИЗ СТАТИСТИКИ
# ============================================================================

@router.callback_query(F.data == "show_my_rating")
async def show_my_rating_callback(callback: CallbackQuery, session: AsyncSession):
    """Обработчик кнопки 'Мой рейтинг' из статистики"""
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language if user else "ru"

    # Получаем данные
    season = await get_current_season(session)

    if not season:
        no_season_text = {
            "ru": "❌ Месячный рейтинг пока не активен.",
            "uk": "❌ Місячний рейтинг поки не активний.",
            "en": "❌ Monthly leaderboard is not active yet.",
            "tr": "❌ Aylık sıralama henüz aktif değil."
        }
        await callback.message.answer(no_season_text.get(lang, no_season_text["ru"]))
        return

    leaderboard = await get_monthly_leaderboard(session, season_id=season.id, limit=10)
    user_rank = await get_user_monthly_rank(user.id, session, season_id=season.id)

    # Формируем текст
    text = format_monthly_leaderboard(leaderboard, user_rank, season, user.id, lang)

    # Клавиатура с вкладками
    keyboard = get_leaderboard_keyboard(lang, current_tab="monthly")

    # Редактируем сообщение
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception as e:
        print(f"⚠️ Не удалось отредактировать: {e}")
        await callback.message.answer(text, reply_markup=keyboard)


# ============================================================================
# ПЕРЕКЛЮЧЕНИЕ НА МЕСЯЧНЫЙ РЕЙТИНГ
# ============================================================================

@router.callback_query(F.data == "leaderboard_monthly")
async def switch_to_monthly(callback: CallbackQuery, session: AsyncSession):
    """Переключиться на месячный рейтинг (из вкладок)"""
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language if user else "ru"

    # Получаем данные
    season = await get_current_season(session)

    if not season:
        await callback.message.edit_text("❌ Рейтинг не активен")
        return

    leaderboard = await get_monthly_leaderboard(session, season_id=season.id, limit=10)
    user_rank = await get_user_monthly_rank(user.id, session, season_id=season.id)

    # Формируем текст
    text = format_monthly_leaderboard(leaderboard, user_rank, season, user.id, lang)

    # Обновляем сообщение
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_leaderboard_keyboard(lang, current_tab="monthly")
        )
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")