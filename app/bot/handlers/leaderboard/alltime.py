"""
Мой рейтинг — вкладка «За всё время»
Персональная карточка lifetime достижений
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.services.monthly_leaderboard_service import get_lifetime_leaderboard
from app.bot.handlers.leaderboard.utils import get_leaderboard_keyboard_text

router = Router()


def get_rating_keyboard(lang: str, current_tab: str = "alltime") -> InlineKeyboardMarkup:
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
                    callback_data="leaderboard_table_alltime"
                )
            ]
        ]
    )


def build_alltime_card(
    user: User,
    leaderboard: list,
    lang: str
) -> str:
    """Персональная карточка за всё время"""

    user_id = user.id

    # ═══════════════ ЗАГОЛОВОК ═══════════════
    text = "🏆 <b>Мой рейтинг — За всё время</b>\n\n"

    # ═══════════════ ПОЗИЦИЯ ═══════════════
    user_rank_num = None
    if leaderboard:
        for entry in leaderboard:
            if entry["user_id"] == user_id:
                user_rank_num = entry["rank"]
                break

    lifetime_score = user.lifetime_score or 0
    total_wins = user.total_monthly_wins or 0
    words_learned = user.words_learned or 0

    if user_rank_num:
        text += f"📍 Позиция: <b>#{user_rank_num}</b>\n"
    else:
        text += f"📍 Позиция: <b>—</b>\n"

    text += f"💎 Баллы: <b>{lifetime_score}</b>\n\n"

    # ═══════════════ ДОСТИЖЕНИЯ ═══════════════
    text += f"⭐ <b>Твои достижения:</b>\n"
    text += f"├ Побед (1 место): {total_wins}\n"
    text += f"└ Выучено слов: {words_learned}\n"

    # ═══════════════ МОТИВАЦИЯ ═══════════════
    if total_wins == 0 and lifetime_score == 0:
        text += "\n🚀 Начни учить слова — первый шаг самый важный!\n"
    elif total_wins == 0:
        text += "\n🎯 Продолжай — первая победа уже близко!\n"
    elif total_wins >= 3:
        text += "\n🔥 Ты настоящий чемпион!\n"

    # ═══════════════ ПОЯСНЕНИЕ ═══════════════
    text += "\n━━━━━━━━━━━━━━━━━\n"
    text += "🌟 <b>Lifetime баллы — это:</b>\n"
    text += "• Все баллы за все месяцы\n"
    text += "• +100 за 🥇 · +50 за 🥈 · +25 за 🥉\n"

    return text


# ============================================================================
# ПЕРЕКЛЮЧЕНИЕ ВКЛАДКИ: За всё время
# ============================================================================

@router.callback_query(F.data == "rating_alltime")
async def switch_to_alltime(callback: CallbackQuery, session: AsyncSession):
    """Вкладка За всё время — ТОЛЬКО edit"""
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language if user else "ru"

    leaderboard = await get_lifetime_leaderboard(session, limit=10)
    text = build_alltime_card(user, leaderboard, lang)

    await callback.message.edit_text(
        text,
        reply_markup=get_rating_keyboard(lang, "alltime")
    )