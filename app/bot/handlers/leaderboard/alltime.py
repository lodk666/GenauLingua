"""
Рейтинг "За всё время"
Отображает топ-10 игроков по lifetime баллам
УЛУЧШЕННАЯ ВЕРСИЯ — понятная, красивая, интересная
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.services.monthly_leaderboard_service import get_lifetime_leaderboard
from app.bot.handlers.leaderboard.utils import (
    get_user_title,
    get_leaderboard_keyboard_text,
    get_localized_text
)

router = Router()


def format_alltime_card(entry: dict, rank: int, is_current_user: bool, lang: str = "ru") -> str:
    """
    Форматировать карточку пользователя в рейтинге "за всё время"

    Args:
        entry: данные пользователя
        rank: позиция в рейтинге
        is_current_user: это текущий пользователь?
        lang: язык интерфейса

    Returns:
        Красиво оформленная карточка
    """
    display_name = entry["display_name"]
    lifetime_score = entry["lifetime_score"]
    total_wins = entry.get("total_wins", 0)

    # Эмодзи для топ-3
    if rank == 1:
        rank_emoji = "🥇"
    elif rank == 2:
        rank_emoji = "🥈"
    elif rank == 3:
        rank_emoji = "🥉"
    else:
        rank_emoji = f"{rank}."

    # Титул (win streak или слова)
    title = get_user_title(
        entry.get("win_streak"),
        entry.get("words_learned", 0)
    )
    title_str = f" {title}" if title else ""

    # ТОП-3 — только медали, БЕЗ титулов
    if rank <= 3:
        if is_current_user:
            card = f"{rank_emoji} <b>{display_name}</b>\n"
            card += f"   💎 {lifetime_score} баллов"
        else:
            card = f"{rank_emoji} {display_name}\n"
            card += f"   💎 {lifetime_score} баллов"
    else:
        # Остальные — с титулами
        wins_text = "побед" if lang in ["ru", "uk"] else "wins"

        if is_current_user:
            card = f"{rank_emoji} <b>{display_name}{title_str}</b> — {lifetime_score} баллов"
        else:
            card = f"{rank_emoji} {display_name}{title_str} — {lifetime_score} баллов"

    return card


def get_leaderboard_keyboard(lang: str, current_tab: str = "alltime") -> InlineKeyboardMarkup:
    """Клавиатура переключения между вкладками"""
    texts = get_leaderboard_keyboard_text(lang, current_tab)

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=texts['monthly'], callback_data="leaderboard_monthly"),
                InlineKeyboardButton(text=texts['alltime'], callback_data="leaderboard_alltime")
            ]
        ]
    )


@router.callback_query(F.data == "leaderboard_alltime")
async def switch_to_alltime(callback: CallbackQuery, session: AsyncSession):
    """Переключиться на рейтинг 'за всё время'"""
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language if user else "ru"

    # Получаем всё-время рейтинг
    leaderboard = await get_lifetime_leaderboard(session, limit=10)

    # Формируем текст
    title_text = get_localized_text("title_alltime", lang)
    text = f"<b>{title_text}</b>\n\n"

    if not leaderboard:
        no_data_text = {
            "ru": "🚧 Пока нет данных...\nПройди первую викторину!",
            "uk": "🚧 Поки немає даних...\nПройди першу вікторину!",
            "en": "🚧 No data yet...\nTake your first quiz!",
            "tr": "🚧 Henüz veri yok...\nİlk testi çöz!"
        }
        text += no_data_text.get(lang, no_data_text["ru"]) + "\n"
    else:
        # Топ-10
        for entry in leaderboard:
            rank = entry["rank"]
            is_current_user = (entry["user_id"] == user.id)

            card = format_alltime_card(entry, rank, is_current_user, lang)
            text += f"{card}\n"

        # Информация о текущем пользователе
        current_user_entry = None
        for entry in leaderboard:
            if entry["user_id"] == user.id:
                current_user_entry = entry
                break

        if current_user_entry:
            text += "\n" + "━" * 17 + "\n"

            rank = current_user_entry["rank"]
            score = current_user_entry["lifetime_score"]
            total_wins = current_user_entry.get("total_wins", 0)
            words = current_user_entry.get("words_learned", 0)

            # Позиция
            if lang in ["ru", "uk"]:
                text += f"📍 <b>Твоя позиция: #{rank}</b>\n"
            else:
                text += f"📍 <b>Your position: #{rank}</b>\n"

            # Баллы
            text += f"💎 Баллы: {score}\n"

            # Достижения
            wins_text = "побед в топ-3" if lang in ["ru", "uk"] else "top-3 wins"
            words_text = "выучено слов" if lang in ["ru", "uk"] else "words learned"

            text += f"🏆 {total_wins} {wins_text}\n"
            text += f"📚 {words} {words_text}\n\n"

        # Пояснение — красиво и понятно
        text += "━" * 17 + "\n"

        if lang in ["ru", "uk"]:
            text += "💡 <b>Lifetime баллы — это:</b>\n"
            text += "• Все баллы за все месяцы\n"
            text += "• +100 за 🥇 место\n"
            text += "• +50 за 🥈 место\n"
            text += "• +25 за 🥉 место\n"
        else:
            text += "💡 <b>Lifetime points:</b>\n"
            text += "• All points from all months\n"
            text += "• +100 for 🥇 place\n"
            text += "• +50 for 🥈 place\n"
            text += "• +25 for 🥉 place\n"

    # Обновляем сообщение
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_leaderboard_keyboard(lang, current_tab="alltime")
        )
    except Exception as e:
        print(f"⚠️ Ошибка редактирования: {e}")
        await callback.message.answer(
            text,
            reply_markup=get_leaderboard_keyboard(lang, current_tab="alltime")
        )