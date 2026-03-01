"""
Статистика и прогресс пользователя с локализацией
"""

import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.models import User, QuizSession
from app.bot.keyboards import get_main_menu_keyboard
from app.locales import get_text, pluralize
from app.services.quiz_service import (
    get_user_progress_stats,
    get_user_progress_stats_all_levels,
)

router = Router()

MODE_DICT = {
    "de_to_ru": "🇩🇪 DE → 🏴 RU",
    "ru_to_de": "🏴 RU → 🇩🇪 DE",
    "de_to_uk": "🇩🇪 DE → 🇺🇦 UK",
    "uk_to_de": "🇺🇦 UK → 🇩🇪 DE",
}


def get_stats_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Клавиатура под статистикой с кнопкой Рейтинг"""
    button_text = "🏆 Рейтинг"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=button_text,
            callback_data="show_leaderboard"
        )]
    ])


async def delete_messages_fast(bot, chat_id: int, start_id: int, end_id: int):
    tasks = []
    for msg_id in range(start_id, end_id):
        tasks.append(bot.delete_message(chat_id=chat_id, message_id=msg_id))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    deleted = sum(1 for r in results if not isinstance(r, Exception))
    print(f"   🧹 Удалено {deleted}/{len(tasks)} сообщений")


async def ensure_anchor(message: Message, session: AsyncSession, user: User, emoji: str = "🤖"):
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


@router.callback_query(F.data == "back_to_stats")
async def back_to_stats_callback(callback: CallbackQuery, session: AsyncSession):
    """Возврат к статистике из рейтинга"""
    await callback.answer()
    await show_statistics(callback.message, session)


@router.message(Command("stats"))
@router.message(F.text.in_(["📊 Статистика", "📊 Статистика", "📊 Statistics", "📊 İstatistikler"]))
async def show_statistics(message: Message, session: AsyncSession):
    """Показ детальной статистики"""
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

    # Получаем статистику
    try:
        overall_progress = await get_user_progress_stats_all_levels(user_id, session)
    except Exception as e:
        print(f"⚠️ Ошибка общей статистики: {e}")
        overall_progress = {'total_words': 0, 'seen_words': 0, 'learned_words': 0, 'struggling_words': 0, 'new_words': 0}

    try:
        progress = await get_user_progress_stats(user_id, user.level, session)
    except Exception as e:
        print(f"⚠️ Ошибка статистики уровня: {e}")
        progress = {'total_words': 0, 'seen_words': 0, 'learned_words': 0, 'struggling_words': 0, 'new_words': 0}

    # Викторины текущего уровня
    result = await session.execute(
        select(QuizSession)
        .where(
            QuizSession.user_id == user_id,
            QuizSession.level == user.level,
            QuizSession.completed_at.isnot(None)
        )
        .order_by(QuizSession.started_at.desc())
    )
    all_level_sessions = result.scalars().all()
    level_sessions = all_level_sessions[:5]

    # ФОРМИРУЕМ ТЕКСТ СТАТИСТИКИ
    stats_text = f"{get_text('stats_title', lang)}\n"

    # Блок 0: Вся база (все уровни)
    overall_total = overall_progress['total_words']
    overall_learned = overall_progress['learned_words']
    overall_in_progress = overall_progress['seen_words'] - overall_learned
    overall_new = overall_progress['new_words']
    overall_difficult = overall_progress['struggling_words']

    word_form = pluralize(overall_total, ("слово", "слова", "слів") if lang == "uk" else ("слово", "слова", "слов"))
    stats_text += f"📚 Вся база ({overall_total} {word_form})\n" if lang == "ru" else f"📚 Вся база ({overall_total} {word_form})\n"
    stats_text += get_text("stats_learned", lang, count=overall_learned) + "\n"
    stats_text += get_text("stats_in_progress", lang, count=overall_in_progress) + "\n"
    stats_text += get_text("stats_new", lang, count=overall_new) + "\n"
    stats_text += get_text("stats_difficult", lang, count=overall_difficult) + "\n\n"

    # Блок 1: Текущий уровень + режим
    mode = MODE_DICT.get(user.translation_mode.value, user.translation_mode.value)
    total = progress['total_words']
    learned = progress['learned_words']
    in_progress = progress['seen_words'] - learned
    new = progress['new_words']
    difficult = progress['struggling_words']

    word_form = pluralize(total, ("слово", "слова", "слів") if lang == "uk" else ("слово", "слова", "слов"))
    stats_text += f"\n🎯 <b>Рівень {user.level.value}</b> ({total} {word_form})\n" if lang == "uk" else f"\n🎯 <b>Уровень {user.level.value}</b> ({total} {word_form})\n"
    stats_text += get_text("stats_learned", lang, count=learned) + "\n"
    stats_text += get_text("stats_in_progress", lang, count=in_progress) + "\n"
    stats_text += get_text("stats_new", lang, count=new) + "\n"
    stats_text += get_text("stats_difficult", lang, count=difficult) + "\n\n"

    # Блок 2: Викторины
    if all_level_sessions:
        stats_text += get_text("stats_quizzes_title", lang, level=user.level.value) + "\n"

        total_quizzes = len(all_level_sessions)
        total_questions = sum(s.total_questions for s in all_level_sessions)
        total_correct = sum(s.correct_answers for s in all_level_sessions)
        avg_percent = (total_correct / total_questions * 100) if total_questions > 0 else 0
        best_result = max((s.correct_answers / s.total_questions * 100) for s in all_level_sessions) if all_level_sessions else 0

        stats_text += get_text("stats_quizzes_passed", lang, count=total_quizzes) + "\n"
        stats_text += get_text("stats_quizzes_avg", lang, percentage=f"{avg_percent:.1f}") + "\n"
        stats_text += get_text("stats_quizzes_best", lang, percentage=f"{best_result:.1f}") + "\n\n"
    else:
        stats_text += get_text("stats_quizzes_title", lang, level=user.level.value) + "\n"
        stats_text += get_text("stats_quizzes_none", lang) + "\n\n"

    # Блок 3: Активность
    stats_text += get_text("stats_activity_title", lang) + "\n"
    stats_text += get_text("stats_streak", lang, days=user.streak_days) + "\n\n"

    # Блок 4: Последние викторины
    if level_sessions:
        stats_text += "━━━━━━━━━━━━━━━━━\n"
        stats_text += get_text("stats_recent_title", lang) + "\n\n"

        for i, s in enumerate(level_sessions, 1):
            percentage = (s.correct_answers / s.total_questions * 100) if s.total_questions > 0 else 0
            date_str = s.started_at.strftime("%d.%m %H:%M")

            if percentage >= 80:
                emoji = "🏆"
            elif percentage >= 60:
                emoji = "👍"
            else:
                emoji = "📝"

            stats_text += f"{emoji} {date_str} • {s.correct_answers}/{s.total_questions} ({percentage:.0f}%)\n"

    # Пояснение
    stats_text += "\n━━━━━━━━━━━━━━━━━\n"
    stats_text += get_text("stats_learned_explanation", lang)

    # Создаём якорь и очищаем старое
    old_anchor_id, new_anchor_id = await ensure_anchor(message, session, user, emoji="📊")

    if old_anchor_id:
        current_msg_id = message.message_id
        await delete_messages_fast(message.bot, message.chat.id, old_anchor_id, current_msg_id)

    # ОТПРАВЛЯЕМ С КНОПКОЙ РЕЙТИНГ
    await message.answer(
        stats_text,
        reply_markup=get_stats_keyboard(lang)
    )