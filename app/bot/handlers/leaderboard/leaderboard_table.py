"""
Таблица лидеров — топ-10 игроков — ЛОКАЛИЗОВАНО
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
from app.locales import get_text

router = Router()


def get_table_keyboard(lang: str, current_tab: str = "monthly") -> InlineKeyboardMarkup:
    texts = get_leaderboard_keyboard_text(lang, current_tab)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=texts['monthly'], callback_data="table_monthly"),
                InlineKeyboardButton(text=texts['alltime'], callback_data="table_alltime")
            ],
            [
                InlineKeyboardButton(
                    text=get_text("btn_back_to_rating", lang),
                    callback_data="rating_monthly"
                )
            ]
        ]
    )


def _rank_emoji(rank: int) -> str:
    if rank == 1: return "🥇"
    elif rank == 2: return "🥈"
    elif rank == 3: return "🥉"
    return f"{rank}."


def _shorten_name(name: str, max_len: int = 15) -> str:
    if len(name) <= max_len:
        return name
    first = name.split()[0]
    if len(first) <= max_len:
        return first
    return first[:max_len - 1] + "…"


def build_monthly_table(leaderboard: list, user_rank: dict, season, user_id: int, lang: str) -> str:
    month_name = format_month_name(season.month, lang)
    pts = get_text("table_points", lang)

    text = get_text("table_title_monthly", lang, month=month_name, year=season.year) + "\n\n"

    if not leaderboard:
        text += get_text("table_empty", lang) + "\n"
        return text

    user_in_top = False
    for entry in leaderboard:
        rank = entry["rank"]
        name = _shorten_name(entry["display_name"])
        score = entry["monthly_score"]
        emoji = _rank_emoji(rank)

        title = ""
        if rank > 3:
            t = get_user_title(entry.get("win_streak"), entry.get("monthly_words", 0))
            if t: title = f" {t}"

        is_me = entry["user_id"] == user_id
        if is_me:
            user_in_top = True
            text += f"{emoji} <b>{name}{title}</b> — {score} {pts}\n"
        else:
            text += f"{emoji} {name}{title} — {score} {pts}\n"

    text += "\n" + "━" * 17 + "\n"

    if user_rank:
        rank = user_rank['rank']
        score = user_rank['monthly_score']
        total = user_rank.get('total_users', 1)

        if user_in_top:
            text += get_text("table_you_in_top", lang, rank=rank, total=total) + "\n"
        else:
            text += get_text("table_you_not_in_top", lang, rank=rank, total=total, score=score) + "\n"
    else:
        text += get_text("table_you_not_ranked", lang) + "\n"

    return text


def build_alltime_table(leaderboard: list, user: User, lang: str) -> str:
    user_id = user.id
    pts = get_text("table_points", lang)

    text = get_text("table_title_alltime", lang) + "\n\n"

    if not leaderboard:
        text += get_text("table_empty", lang) + "\n"
        return text

    user_in_top = False
    for entry in leaderboard:
        rank = entry["rank"]
        name = _shorten_name(entry["display_name"])
        score = entry["lifetime_score"]
        emoji = _rank_emoji(rank)

        title = ""
        if rank > 3:
            t = get_user_title(entry.get("win_streak"), entry.get("words_learned", 0))
            if t: title = f" {t}"

        is_me = entry["user_id"] == user_id
        if is_me:
            user_in_top = True
            text += f"{emoji} <b>{name}{title}</b> — {score} {pts}\n"
        else:
            text += f"{emoji} {name}{title} — {score} {pts}\n"

    text += "\n" + "━" * 17 + "\n"

    user_rank_num = None
    for entry in leaderboard:
        if entry["user_id"] == user_id:
            user_rank_num = entry["rank"]
            break

    lifetime = user.lifetime_score or 0
    total = len(leaderboard)

    if user_rank_num:
        if user_in_top:
            text += get_text("table_you_in_top", lang, rank=user_rank_num, total=total) + "\n"
        else:
            text += get_text("table_you_not_in_top", lang, rank=user_rank_num, total=total, score=lifetime) + "\n"
    else:
        if lifetime > 0:
            text += get_text("table_you_outside", lang, score=lifetime) + "\n"
        else:
            text += get_text("table_you_not_ranked", lang) + "\n"

    return text


@router.callback_query(F.data == "leaderboard_table_monthly")
async def show_table_monthly(callback: CallbackQuery, session: AsyncSession):
    await callback.answer()
    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language if user else "ru"
    season = await get_current_season(session)

    if not season:
        await callback.message.edit_text(get_text("rating_not_active", lang))
        return

    leaderboard = await get_monthly_leaderboard(session, season_id=season.id, limit=10)
    user_rank = await get_user_monthly_rank(user.id, session, season_id=season.id)
    text = build_monthly_table(leaderboard, user_rank, season, user.id, lang)
    await callback.message.edit_text(text, reply_markup=get_table_keyboard(lang, "monthly"))


@router.callback_query(F.data == "leaderboard_table_alltime")
async def show_table_alltime(callback: CallbackQuery, session: AsyncSession):
    await callback.answer()
    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language if user else "ru"

    leaderboard = await get_lifetime_leaderboard(session, limit=10)
    text = build_alltime_table(leaderboard, user, lang)
    await callback.message.edit_text(text, reply_markup=get_table_keyboard(lang, "alltime"))


@router.callback_query(F.data == "table_monthly")
async def switch_table_to_monthly(callback: CallbackQuery, session: AsyncSession):
    await callback.answer()
    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language if user else "ru"
    season = await get_current_season(session)

    if not season:
        await callback.message.edit_text(get_text("rating_not_active", lang))
        return

    leaderboard = await get_monthly_leaderboard(session, season_id=season.id, limit=10)
    user_rank = await get_user_monthly_rank(user.id, session, season_id=season.id)
    text = build_monthly_table(leaderboard, user_rank, season, user.id, lang)
    await callback.message.edit_text(text, reply_markup=get_table_keyboard(lang, "monthly"))


@router.callback_query(F.data == "table_alltime")
async def switch_table_to_alltime(callback: CallbackQuery, session: AsyncSession):
    await callback.answer()
    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language if user else "ru"

    leaderboard = await get_lifetime_leaderboard(session, limit=10)
    text = build_alltime_table(leaderboard, user, lang)
    await callback.message.edit_text(text, reply_markup=get_table_keyboard(lang, "alltime"))