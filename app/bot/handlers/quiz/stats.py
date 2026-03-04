"""
Статистика и прогресс пользователя с локализацией
УЛУЧШЕННАЯ ВЕРСИЯ — информативная, понятная, интересная
"""

import asyncio
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
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
    "de_to_ru": "🇩🇪 → 🏴",
    "ru_to_de": "🏴 → 🇩🇪",
    "de_to_uk": "🇩🇪 → 🇺🇦",
    "uk_to_de": "🇺🇦 → 🇩🇪",
    "de_to_en": "🇩🇪 → 🇬🇧",
    "en_to_de": "🇬🇧 → 🇩🇪",
    "de_to_tr": "🇩🇪 → 🇹🇷",
    "tr_to_de": "🇹🇷 → 🇩🇪",
    "DE_TO_RU": "🇩🇪 → 🏴",
    "RU_TO_DE": "🏴 → 🇩🇪",
    "DE_TO_UK": "🇩🇪 → 🇺🇦",
    "UK_TO_DE": "🇺🇦 → 🇩🇪",
    "DE_TO_EN": "🇩🇪 → 🇬🇧",
    "EN_TO_DE": "🇬🇧 → 🇩🇪",
    "DE_TO_TR": "🇩🇪 → 🇹🇷",
    "TR_TO_DE": "🇹🇷 → 🇩🇪",
}


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


def get_stats_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура под статистикой с кнопкой рейтинга"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🏆 Мой рейтинг" if lang == "ru" else "🏆 Мій рейтинг" if lang == "uk" else "🏆 My rank" if lang == "en" else "🏆 Sıralamam",
                callback_data="show_my_rating"
            )]
        ]
    )


def create_progress_bar(current: int, total: int, length: int = 10) -> str:
    """Создать визуальный прогресс-бар"""
    if total == 0:
        return "░" * length + " 0%"

    percentage = min(100, int((current / total) * 100))
    filled = int((current / total) * length)
    empty = length - filled

    bar = "▓" * filled + "░" * empty
    return f"{bar} {percentage}%"


def get_achievement_emoji(percentage: float) -> str:
    """Получить эмодзи достижения по проценту"""
    if percentage >= 95:
        return "🏆"
    elif percentage >= 85:
        return "🥇"
    elif percentage >= 75:
        return "🥈"
    elif percentage >= 60:
        return "🥉"
    else:
        return "📝"


@router.message(Command("stats"))
@router.message(F.text.in_(["📊 Статистика", "📊 Статистика", "📊 Statistics", "📊 İstatistikler"]))
async def show_statistics(message: Message, session: AsyncSession):
    print("🟢 STATS.PY: show_statistics() вызвана")
    user_id = message.from_user.id
    """Показ детальной статистики — УЛУЧШЕННАЯ ВЕРСИЯ"""
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

    # ========================================================================
    # ФОРМИРУЕМ НОВЫЙ УЛУЧШЕННЫЙ ТЕКСТ СТАТИСТИКИ
    # ========================================================================

    stats_text = f"📊 <b>Твоя статистика</b>\n\n" if lang in ["ru", "uk"] else f"📊 <b>Your statistics</b>\n\n"

    # Текущий уровень
    mode = MODE_DICT.get(user.translation_mode.value, "🇩🇪 → 🏴")
    total = progress['total_words']
    learned = progress['learned_words']

    # Прогресс-бар для текущего уровня
    progress_bar = create_progress_bar(learned, total, length=12)

    stats_text += f"🎯 <b>{user.level.value}</b> · {mode}\n"
    stats_text += f"{progress_bar}\n"
    stats_text += f"└─ Выучено <b>{learned}</b> из {total}\n\n"

    # Детализация слов (компактно в одну строку)
    in_progress = progress['seen_words'] - learned
    new = progress['new_words']
    difficult = progress['struggling_words']

    stats_text += f"🔄 В процессе: {in_progress}  ·  🆕 Новых: {new}  ·  ⚠️ Сложных: {difficult}\n\n"

    # ДОСТИЖЕНИЯ
    overall_learned = overall_progress['learned_words']

    if overall_learned >= 500:
        words_emoji = "🏆"
    elif overall_learned >= 200:
        words_emoji = "🥇"
    elif overall_learned >= 100:
        words_emoji = "🥈"
    elif overall_learned >= 50:
        words_emoji = "🥉"
    else:
        words_emoji = "⭐"

    streak_text = f"{user.streak_days} дней подряд" if lang == "ru" else f"{user.streak_days} днів поспіль" if lang == "uk" else f"{user.streak_days} days in a row"

    stats_text += f"{words_emoji} <b>Твои достижения</b>\n" if lang in ["ru", "uk"] else f"{words_emoji} <b>Your achievements</b>\n"
    stats_text += f"├─ Выучено слов: <b>{overall_learned}</b>\n" if lang in ["ru", "uk"] else f"├─ Words learned: <b>{overall_learned}</b>\n"
    stats_text += f"└─ Стрик: <b>{streak_text}</b>\n\n"

    # ВИКТОРИНЫ
    if all_level_sessions:
        total_quizzes = len(all_level_sessions)
        total_questions = sum(s.total_questions for s in all_level_sessions)
        total_correct = sum(s.correct_answers for s in all_level_sessions)
        avg_percent = (total_correct / total_questions * 100) if total_questions > 0 else 0
        best_result = max((s.correct_answers / s.total_questions * 100) for s in all_level_sessions) if all_level_sessions else 0

        achievement_emoji = get_achievement_emoji(avg_percent)

        stats_text += f"{achievement_emoji} <b>Викторины ({user.level.value})</b>\n"
        stats_text += f"├─ Пройдено: <b>{total_quizzes}</b>\n"
        stats_text += f"├─ Средний результат: <b>{avg_percent:.0f}%</b>\n"
        stats_text += f"└─ Лучший результат: <b>{best_result:.0f}%</b>\n\n"
    else:
        stats_text += f"📝 <b>Викторины ({user.level.value})</b>\n"
        stats_text += "└─ Пока нет пройденных викторин\n\n"

    # ПОСЛЕДНИЕ ВИКТОРИНЫ
    if all_level_sessions:
        stats_text += "📈 <b>Последние викторины</b>\n"

        for s in all_level_sessions[:3]:
            percentage = (s.correct_answers / s.total_questions * 100) if s.total_questions > 0 else 0
            date_str = s.started_at.strftime("%d.%m")
            emoji = get_achievement_emoji(percentage)
            stats_text += f"{emoji} {date_str} — {s.correct_answers}/{s.total_questions} ({percentage:.0f}%)\n"

        stats_text += "\n"

    # ОБЩИЙ ПРОГРЕСС
    overall_total = overall_progress['total_words']

    if overall_total > 0:
        overall_bar = create_progress_bar(overall_learned, overall_total, length=12)

        stats_text += "🌍 <b>Общий прогресс</b>\n"
        stats_text += f"{overall_bar}\n"
        stats_text += f"└─ Выучено <b>{overall_learned}</b> из {overall_total} слов\n\n"

    # МОТИВАЦИЯ
    if learned == 0:
        cta = "💪 Начни учить слова — первый шаг самый важный!" if lang in ["ru", "uk"] else "💪 Start learning — the first step is the most important!"
    elif learned < total * 0.3:
        cta = "🚀 Отличное начало! Продолжай в том же духе!" if lang in ["ru", "uk"] else "🚀 Great start! Keep going!"
    elif learned < total * 0.7:
        cta = "🔥 Ты на полпути! Не останавливайся!" if lang in ["ru", "uk"] else "🔥 Halfway there! Don't stop!"
    else:
        cta = "🏆 Почти у цели! Ты молодец!" if lang in ["ru", "uk"] else "🏆 Almost there! Great job!"

    stats_text += f"{cta}\n\n"

    # ПОЯСНЕНИЕ
    explanation_text = {
        "ru": "—————————————————————\nСлово выучено = 3 правильных ответа подряд",
        "uk": "—————————————————————\nСлово вивчено = 3 правильних відповіді поспіль",
        "en": "—————————————————————\nWord learned = 3 correct answers in a row",
        "tr": "—————————————————————\nÖğrenildi = üst üste 3 doğru cevap"
    }

    stats_text += explanation_text.get(lang, explanation_text["ru"])

    # Создаём якорь и очищаем старое
    old_anchor_id, new_anchor_id = await ensure_anchor(message, session, user, emoji="📊")

    if old_anchor_id:
        current_msg_id = message.message_id
        await delete_messages_fast(message.bot, message.chat.id, old_anchor_id, current_msg_id)

    # Показываем статистику с кнопкой рейтинга
    await message.answer(stats_text, reply_markup=get_stats_keyboard(lang))