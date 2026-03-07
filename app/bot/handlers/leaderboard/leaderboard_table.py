"""
Таблица лидеров — топ-10 игроков
Вход через кнопку «📊 Таблица лидеров» из «Мой рейтинг»
Вкладки: Месяц / За всё время
Кнопка: Назад к рейтингу
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.services.monthly_leaderboard_service import (
    get_monthly_leaderboard,
    get_user_monthly_rank,
    get_current_season,
    get_lifetime_leaderboard
)
from app.bot.handlers.leaderboard.utils import (
    format_month_name,
    get_user_title,
    get_leaderboard_keyboard_text
)

router = Router()


# ============================================================================
# КЛАВИАТУРА
# ============================================================================

def get_table_keyboard(lang: str, current_tab: str = "monthly") -> InlineKeyboardMarkup:
    """Клавиатура таблицы: вкладки + назад"""
    texts = get_leaderboard_keyboard_text(lang, current_tab)

    back_text = {
        "ru": "◀️ Назад к рейтингу",
        "uk": "◀️ Назад до рейтингу",
        "en": "◀️ Back to rating",
        "tr": "◀️ Sıralamaya geri dön"
    }.get(lang, "◀️ Назад к рейтингу")

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=texts['monthly'], callback_data="table_monthly"),
                InlineKeyboardButton(text=texts['alltime'], callback_data="table_alltime")
            ],
            [
                InlineKeyboardButton(text=back_text, callback_data="rating_monthly")
            ]
        ]
    )


# ============================================================================
# ФОРМАТИРОВАНИЕ
# ============================================================================

def _rank_emoji(rank: int) -> str:
    if rank == 1:
        return "🥇"
    elif rank == 2:
        return "🥈"
    elif rank == 3:
        return "🥉"
    return f"{rank}."


def _shorten_name(name: str, max_len: int = 15) -> str:
    """Обрезать длинное имя чтобы таблица не ломалась"""
    if len(name) <= max_len:
        return name
    first = name.split()[0]
    if len(first) <= max_len:
        return first
    return first[:max_len - 1] + "…"


def build_monthly_table(
    leaderboard: list,
    user_rank: dict,
    season,
    user_id: int,
    lang: str
) -> str:
    """Таблица лидеров за месяц"""

    month_name = format_month_name(season.month, lang)

    text = f"📊 <b>Таблица лидеров — {month_name} {season.year}</b>\n\n"

    if not leaderboard:
        text += "Пока никто не участвует.\nПройди викторину первым! 💪\n"
        return text

    # Топ-10
    user_in_top = False
    for entry in leaderboard:
        rank = entry["rank"]
        name = _shorten_name(entry["display_name"])
        score = entry["monthly_score"]
        emoji = _rank_emoji(rank)

        # Титул для 4+ мест
        title = ""
        if rank > 3:
            title_emoji = get_user_title(
                entry.get("win_streak"),
                entry.get("monthly_words", 0)
            )
            if title_emoji:
                title = f" {title_emoji}"

        is_me = entry["user_id"] == user_id
        if is_me:
            user_in_top = True
            text += f"{emoji} <b>{name}{title}</b> — {score} баллов\n"
        else:
            text += f"{emoji} {name}{title} — {score} баллов\n"

    # Если юзер не в топ-10 — показываем его отдельно
    text += "\n" + "━" * 17 + "\n"

    if user_rank:
        rank = user_rank['rank']
        score = user_rank['monthly_score']
        total = user_rank.get('total_users', 1)

        if user_in_top:
            text += f"📍 Ты: <b>#{rank}</b> из {total}\n"
        else:
            text += f"📍 Ты: <b>#{rank}</b> из {total} — {score} баллов\n"
    else:
        text += "📍 Ты ещё не в рейтинге\n"

    return text


def build_alltime_table(
    leaderboard: list,
    user: User,
    lang: str
) -> str:
    """Таблица лидеров за всё время"""

    text = "📊 <b>Таблица лидеров — За всё время</b>\n\n"

    if not leaderboard:
        text += "Пока нет данных.\nПройди викторину первым! 💪\n"
        return text

    user_id = user.id
    user_in_top = False

    for entry in leaderboard:
        rank = entry["rank"]
        name = _shorten_name(entry["display_name"])
        score = entry["lifetime_score"]
        emoji = _rank_emoji(rank)

        # Титул для 4+ мест
        title = ""
        if rank > 3:
            title_emoji = get_user_title(
                entry.get("win_streak"),
                entry.get("words_learned", 0)
            )
            if title_emoji:
                title = f" {title_emoji}"

        is_me = entry["user_id"] == user_id
        if is_me:
            user_in_top = True
            text += f"{emoji} <b>{name}{title}</b> — {score} баллов\n"
        else:
            text += f"{emoji} {name}{title} — {score} баллов\n"

    # Позиция юзера
    text += "\n" + "━" * 17 + "\n"

    user_rank_num = None
    for entry in leaderboard:
        if entry["user_id"] == user_id:
            user_rank_num = entry["rank"]
            break

    lifetime = user.lifetime_score or 0

    if user_rank_num:
        if user_in_top:
            text += f"📍 Ты: <b>#{user_rank_num}</b>\n"
        else:
            text += f"📍 Ты: <b>#{user_rank_num}</b> — {lifetime} баллов\n"
    else:
        if lifetime > 0:
            text += f"📍 Ты: за пределами топ-10 — {lifetime} баллов\n"
        else:
            text += "📍 Ты ещё не в рейтинге\n"

    return text


# ============================================================================
# HANDLERS
# ============================================================================

@router.callback_query(F.data == "leaderboard_table_monthly")
async def show_table_monthly(callback: CallbackQuery, session: AsyncSession):
    """Вход в таблицу из «Мой рейтинг» (вкладка Месяц)"""
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language if user else "ru"
    season = await get_current_season(session)

    if not season:
        await callback.message.edit_text("❌ Рейтинг не активен")
        return

    leaderboard = await get_monthly_leaderboard(session, season_id=season.id, limit=10)
    user_rank = await get_user_monthly_rank(user.id, session, season_id=season.id)
    text = build_monthly_table(leaderboard, user_rank, season, user.id, lang)

    await callback.message.edit_text(text, reply_markup=get_table_keyboard(lang, "monthly"))


@router.callback_query(F.data == "leaderboard_table_alltime")
async def show_table_alltime(callback: CallbackQuery, session: AsyncSession):
    """Вход в таблицу из «Мой рейтинг» (вкладка За всё время)"""
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language if user else "ru"

    leaderboard = await get_lifetime_leaderboard(session, limit=10)
    text = build_alltime_table(leaderboard, user, lang)

    await callback.message.edit_text(text, reply_markup=get_table_keyboard(lang, "alltime"))


@router.callback_query(F.data == "table_monthly")
async def switch_table_to_monthly(callback: CallbackQuery, session: AsyncSession):
    """Переключить таблицу на Месяц"""
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language if user else "ru"
    season = await get_current_season(session)

    if not season:
        await callback.message.edit_text("❌ Рейтинг не активен")
        return

    leaderboard = await get_monthly_leaderboard(session, season_id=season.id, limit=10)
    user_rank = await get_user_monthly_rank(user.id, session, season_id=season.id)
    text = build_monthly_table(leaderboard, user_rank, season, user.id, lang)

    await callback.message.edit_text(text, reply_markup=get_table_keyboard(lang, "monthly"))


@router.callback_query(F.data == "table_alltime")
async def switch_table_to_alltime(callback: CallbackQuery, session: AsyncSession):
    """Переключить таблицу на За всё время"""
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language if user else "ru"

    leaderboard = await get_lifetime_leaderboard(session, limit=10)
    text = build_alltime_table(leaderboard, user, lang)

    await callback.message.edit_text(text, reply_markup=get_table_keyboard(lang, "alltime"))