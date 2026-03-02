""""
Хэндлер месячного рейтинга
app/bot/handlers/quiz/monthly_leaderboard.py
"""

import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.bot.keyboards import get_main_menu_keyboard
from app.locales import get_text
from app.services.monthly_leaderboard_service import (
    get_monthly_leaderboard,
    get_user_monthly_rank,
    get_current_season,
    get_lifetime_leaderboard
)

router = Router()


async def delete_messages_fast(bot, chat_id: int, start_id: int, end_id: int):
    tasks = []
    for msg_id in range(start_id, end_id):
        tasks.append(bot.delete_message(chat_id=chat_id, message_id=msg_id))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    deleted = sum(1 for r in results if not isinstance(r, Exception))
    print(f"   🧹 Удалено {deleted}/{len(tasks)} сообщений")


async def ensure_anchor(message: Message, session: AsyncSession, user: User, emoji: str = "🏆"):
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
    """Клавиатура переключения между месячным и lifetime рейтингом"""
    monthly_text = "• Месяц •" if current_tab == "monthly" else "Месяц"
    lifetime_text = "• Lifetime •" if current_tab == "lifetime" else "Lifetime"

    if lang == "uk":
        monthly_text = "• Місяць •" if current_tab == "monthly" else "Місяць"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=monthly_text, callback_data="leaderboard_monthly"),
                InlineKeyboardButton(text=lifetime_text, callback_data="leaderboard_lifetime")
            ]
        ]
    )


def format_month_name(month: int, lang: str = "ru") -> str:
    """Форматировать название месяца"""
    months_ru = {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
        5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
        9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
    }
    months_uk = {
        1: "Січень", 2: "Лютий", 3: "Березень", 4: "Квітень",
        5: "Травень", 6: "Червень", 7: "Липень", 8: "Серпень",
        9: "Вересень", 10: "Жовтень", 11: "Листопад", 12: "Грудень"
    }

    months = months_uk if lang == "uk" else months_ru
    return months.get(month, str(month))


# ============================================================================
# КОМАНДА /leaderboard И КНОПКА 🏆 РЕЙТИНГ
# ============================================================================

@router.callback_query(F.data == "show_my_rating")
async def show_my_rating_callback(callback: CallbackQuery, session: AsyncSession):
    """Обработчик кнопки 'Мой рейтинг' из статистики"""
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language if user else "ru"

    # Используем callback.message как message для show_monthly_leaderboard_impl
    # Но нужно создать временный Message объект
    await show_monthly_leaderboard_callback(callback, session, user, lang)


async def show_monthly_leaderboard_callback(
    callback: CallbackQuery,
    session: AsyncSession,
    user: User,
    lang: str
):
    """Показать месячный рейтинг через callback (из статистики)"""
    season = await get_current_season(session)

    if not season:
        await callback.message.edit_text(
            "❌ Месячный рейтинг пока не активен." if lang == "ru"
            else "❌ Місячний рейтинг поки не активний.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(
                    text="◀️ Назад" if lang == "ru" else "◀️ Назад",
                    callback_data="back_to_stats"
                )]]
            )
        )
        return

    # Получаем рейтинг (топ-10)
    leaderboard = await get_monthly_leaderboard(session, season_id=season.id, limit=10)
    user_rank = await get_user_monthly_rank(user.id, session, season_id=season.id)

    # Формируем текст
    month_name = format_month_name(season.month, lang)
    text = f"🏆 <b>Рейтинг {month_name} {season.year}</b>\n\n"

    if not leaderboard:
        text += "Пока никто не участвует в рейтинге.\nПройди викторину первым!\n\n" if lang == "ru" else "Поки ніхто не бере участь у рейтингу.\nПройди вікторину першим!\n\n"
    else:
        for entry in leaderboard:
            rank = entry["rank"]
            display_name = entry["display_name"]
            score = entry["monthly_score"]
            quizzes = entry["monthly_quizzes"]

            if rank == 1:
                emoji = "🥇"
            elif rank == 2:
                emoji = "🥈"
            elif rank == 3:
                emoji = "🥉"
            else:
                emoji = f"{rank}."

            win_streak_emoji = ""
            if entry.get("win_streak"):
                win_streak_emoji = entry["win_streak"].get("emoji", "")

            if entry["user_id"] == user.id:
                text += f"➤ <b>{emoji} {display_name}</b> {win_streak_emoji} — {score} баллов ({quizzes} викторин)\n"
            else:
                text += f"{emoji} {display_name} {win_streak_emoji} — {score} баллов ({quizzes} викторин)\n"

        text += "\n"

    if user_rank:
        rank = user_rank['rank']
        score = user_rank['monthly_score']
        percentile = user_rank.get('percentile', 0)

        text += f"📍 <b>Твоя позиция: #{rank}</b>\n"
        text += f"💎 Баллы: {score}\n"
        text += f"📊 Топ {percentile:.0f}%\n"
    else:
        text += "📍 Ты еще не участвуешь в рейтинге.\nПройди первую викторину!\n"

    text += "\n━━━━━━━━━━━━━━━━━\n"
    text += "📊 <b>Как начисляются баллы:</b>\n"
    text += "• Викторина: 10 баллов\n"
    text += "• Реверс (RU→DE): +5\n"
    text += "• Слово выучено: +2\n"
    text += "• День стрика: +3\n"
    text += "• Средний ≥90%: +50\n"
    text += "• Средний ≥80%: +30\n"

    # Клавиатура с вкладками и кнопкой "Назад"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="• Месяц •", callback_data="leaderboard_monthly"),
                InlineKeyboardButton(text="Lifetime", callback_data="leaderboard_lifetime")
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Назад к статистике" if lang == "ru" else "◀️ Назад до статистики",
                    callback_data="back_to_stats"
                )
            ]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)


@router.message(Command("leaderboard"))
@router.message(F.text.in_(["🏆 Рейтинг", "🏆 Рейтинг"]))  # ru/uk
async def show_leaderboard(message: Message, session: AsyncSession):
    """Показать месячный рейтинг"""
    user_id = message.from_user.id
    user = await session.get(User, user_id)

    try:
        await message.delete()
    except:
        pass

    lang = user.interface_language if user else "ru"

    # Показываем месячный рейтинг по умолчанию
    await show_monthly_leaderboard_impl(message, session, user, lang)


async def show_monthly_leaderboard_impl(
    message: Message,
    session: AsyncSession,
    user: User,
    lang: str
):
    """Реализация отображения месячного рейтинга"""
    # Получаем текущий сезон
    season = await get_current_season(session)

    if not season:
        await message.answer(
            "❌ Месячный рейтинг пока не активен." if lang == "ru"
            else "❌ Місячний рейтинг поки не активний."
        )
        return

    # Получаем рейтинг (топ-10)
    leaderboard = await get_monthly_leaderboard(session, season_id=season.id, limit=10)

    # Получаем позицию пользователя
    user_rank = await get_user_monthly_rank(user.id, session, season_id=season.id)

    # Формируем текст
    month_name = format_month_name(season.month, lang)
    text = f"🏆 <b>Рейтинг {month_name} {season.year}</b>\n\n" if lang == "ru" else f"🏆 <b>Рейтинг {month_name} {season.year}</b>\n\n"

    if not leaderboard:
        text += "Пока никто не участвует в рейтинге.\nПройди викторину первым!\n\n" if lang == "ru" else "Поки ніхто не бере участь у рейтингу.\nПройди вікторину першим!\n\n"
    else:
        # Топ-10
        for entry in leaderboard:
            rank = entry["rank"]
            display_name = entry["display_name"]
            score = entry["monthly_score"]
            quizzes = entry["monthly_quizzes"]

            # Эмодзи для топ-3
            if rank == 1:
                emoji = "🥇"
            elif rank == 2:
                emoji = "🥈"
            elif rank == 3:
                emoji = "🥉"
            else:
                emoji = f"{rank}."

            # Win streak эмодзи
            win_streak_emoji = ""
            if entry.get("win_streak"):
                win_streak_emoji = entry["win_streak"].get("emoji", "")

            # Подсветка текущего пользователя
            if entry["user_id"] == user.id:
                text += f"➤ <b>{emoji} {display_name}</b> {win_streak_emoji} — {score} баллов ({quizzes} викторин)\n"
            else:
                text += f"{emoji} {display_name} {win_streak_emoji} — {score} баллов ({quizzes} викторин)\n"

        text += "\n"

    # Информация о текущем пользователе
    if user_rank:
        rank = user_rank['rank']
        score = user_rank['monthly_score']
        percentile = user_rank.get('percentile', 0)

        text += f"📍 <b>Твоя позиция: #{rank}</b>\n" if lang == "ru" else f"📍 <b>Твоя позиція: #{rank}</b>\n"
        text += f"💎 Баллы: {score}\n" if lang == "ru" else f"💎 Бали: {score}\n"
        text += f"📊 Топ {percentile:.0f}%\n"
    else:
        text += "📍 Ты еще не участвуешь в рейтинге.\nПройди первую викторину!\n" if lang == "ru" else "📍 Ти ще не берешь участь у рейтингу.\nПройди першу вікторину!\n"

    # Формула начисления баллов
    text += "\n━━━━━━━━━━━━━━━━━\n"
    text += "📊 <b>Как начисляются баллы:</b>\n" if lang == "ru" else "📊 <b>Як нараховуються бали:</b>\n"
    text += "• Викторина: 10 баллов\n" if lang == "ru" else "• Вікторина: 10 балів\n"
    text += "• Реверс (RU→DE): +5\n" if lang == "ru" else "• Реверс (UK→DE): +5\n"
    text += "• Слово выучено: +2\n" if lang == "ru" else "• Слово вивчено: +2\n"
    text += "• День стрика: +3\n" if lang == "ru" else "• День стріку: +3\n"
    text += "• Средний ≥90%: +50\n" if lang == "ru" else "• Середній ≥90%: +50\n"
    text += "• Средний ≥80%: +30\n" if lang == "ru" else "• Середній ≥80%: +30\n"

    # Создаём якорь и очищаем старое
    old_anchor_id, new_anchor_id = await ensure_anchor(message, session, user, emoji="🏆")

    if old_anchor_id:
        current_msg_id = message.message_id
        await delete_messages_fast(message.bot, message.chat.id, old_anchor_id, current_msg_id)

    # Показываем с кнопками переключения
    await message.answer(
        text,
        reply_markup=get_leaderboard_keyboard(lang, current_tab="monthly")
    )


async def show_lifetime_leaderboard_impl(
    callback: CallbackQuery,
    session: AsyncSession,
    user: User,
    lang: str
):
    """Реализация отображения lifetime рейтинга (всё время)"""
    # Получаем lifetime рейтинг
    leaderboard = await get_lifetime_leaderboard(session, limit=10)

    # Формируем текст
    text = "🏆 <b>Lifetime Рейтинг</b>\n\n"

    if not leaderboard:
        text += "🚧 Пока нет данных...\n"
    else:
        for entry in leaderboard:
            rank = entry["rank"]
            display_name = entry["display_name"]
            lifetime_score = entry["lifetime_score"]
            total_wins = entry["total_wins"]

            # Эмодзи для топ-3
            if rank == 1:
                emoji = "🥇"
            elif rank == 2:
                emoji = "🥈"
            elif rank == 3:
                emoji = "🥉"
            else:
                emoji = f"{rank}."

            # Win streak
            win_streak_emoji = ""
            if entry.get("win_streak"):
                ws = entry["win_streak"]
                if ws.get("current", 0) > 0:
                    win_streak_emoji = f"🔥×{ws['current']}"

            # Подсветка текущего пользователя
            if entry["user_id"] == user.id:
                text += f"➤ <b>{emoji} {display_name}</b> {win_streak_emoji} — {lifetime_score} lifetime ({total_wins} побед)\n"
            else:
                text += f"{emoji} {display_name} {win_streak_emoji} — {lifetime_score} lifetime ({total_wins} побед)\n"

    await callback.message.edit_text(
        text,
        reply_markup=get_leaderboard_keyboard(lang, current_tab="lifetime")
    )


# ============================================================================
# ПЕРЕКЛЮЧЕНИЕ ВКЛАДОК
# ============================================================================

@router.callback_query(F.data == "leaderboard_monthly")
async def switch_to_monthly(callback: CallbackQuery, session: AsyncSession):
    """Переключиться на месячный рейтинг"""
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language if user else "ru"

    # Получаем текущий сезон
    season = await get_current_season(session)

    if not season:
        await callback.message.edit_text(
            "❌ Месячный рейтинг пока не активен." if lang == "ru"
            else "❌ Місячний рейтинг поки не активний."
        )
        return

    # Получаем рейтинг
    leaderboard = await get_monthly_leaderboard(session, season_id=season.id, limit=10)
    user_rank = await get_user_monthly_rank(user.id, session, season_id=season.id)

    # Формируем текст (аналогично show_monthly_leaderboard_impl)
    month_name = format_month_name(season.month, lang)
    text = f"🏆 <b>Рейтинг {month_name} {season.year}</b>\n\n"

    if not leaderboard:
        text += "Пока никто не участвует в рейтинге.\nПройди викторину первым!\n\n" if lang == "ru" else "Поки ніхто не бере участь у рейтингу.\nПройди вікторину першим!\n\n"
    else:
        for entry in leaderboard:
            rank = entry["rank"]
            display_name = entry["display_name"]
            score = entry["monthly_score"]
            quizzes = entry["monthly_quizzes"]

            if rank == 1:
                emoji = "🥇"
            elif rank == 2:
                emoji = "🥈"
            elif rank == 3:
                emoji = "🥉"
            else:
                emoji = f"{rank}."

            win_streak_emoji = ""
            if entry.get("win_streak"):
                win_streak_emoji = entry["win_streak"].get("emoji", "")

            if entry["user_id"] == user.id:
                text += f"➤ <b>{emoji} {display_name}</b> {win_streak_emoji} — {score} баллов ({quizzes} викторин)\n"
            else:
                text += f"{emoji} {display_name} {win_streak_emoji} — {score} баллов ({quizzes} викторин)\n"

        text += "\n"

    if user_rank:
        rank = user_rank['rank']
        score = user_rank['monthly_score']
        percentile = user_rank.get('percentile', 0)

        text += f"📍 <b>Твоя позиция: #{rank}</b>\n"
        text += f"💎 Баллы: {score}\n"
        text += f"📊 Топ {percentile:.0f}%\n"
    else:
        text += "📍 Ты еще не участвуешь в рейтинге.\nПройди первую викторину!\n"

    text += "\n━━━━━━━━━━━━━━━━━\n"
    text += "📊 <b>Как начисляются баллы:</b>\n"
    text += "• Викторина: 10 баллов\n"
    text += "• Реверс (RU→DE): +5\n"
    text += "• Слово выучено: +2\n"
    text += "• День стрика: +3\n"
    text += "• Средний ≥90%: +50\n"
    text += "• Средний ≥80%: +30\n"

    await callback.message.edit_text(
        text,
        reply_markup=get_leaderboard_keyboard(lang, current_tab="monthly")
    )


@router.callback_query(F.data == "leaderboard_lifetime")
async def switch_to_lifetime(callback: CallbackQuery, session: AsyncSession):
    """Переключиться на lifetime рейтинг"""
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language if user else "ru"

    await show_lifetime_leaderboard_impl(callback, session, user, lang)


@router.callback_query(F.data == "back_to_stats")
async def back_to_stats(callback: CallbackQuery, session: AsyncSession):
    """Вернуться к статистике"""
    await callback.answer()

    # Импортируем функцию показа статистики
    from app.bot.handlers.quiz.stats import show_statistics

    # Создаём фейковое сообщение для вызова show_statistics
    # Просто удаляем текущее сообщение и говорим пользователю нажать кнопку снова
    try:
        await callback.message.delete()
    except:
        pass

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language if user else "ru"

    await callback.message.answer(
        "Нажми 📊 Статистика чтобы вернуться" if lang == "ru" else "Натисни 📊 Статистика щоб повернутися"
    )