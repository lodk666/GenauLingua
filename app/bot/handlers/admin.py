"""
Админ-панель для GenauLingua Bot
Команды доступны только для администратора
"""

import os
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, distinct
from datetime import datetime, timedelta, date
from app.database.models import User, QuizSession, QuizQuestion, UserWord, Word
from app.config import settings

router = Router()

# ID администратора из settings
ADMIN_USER_ID = settings.ADMIN_USER


def is_admin(user_id: int) -> bool:
    """Проверка что пользователь - админ"""
    print(f"🔍 DEBUG: user_id={user_id}, ADMIN_USER_ID={ADMIN_USER_ID}, match={user_id == ADMIN_USER_ID}")
    return user_id == ADMIN_USER_ID


@router.message(Command("admin"))
async def admin_panel(message: Message, session: AsyncSession):
    """Главная админ-панель"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели")
        return

    # Удаляем команду
    try:
        await message.delete()
    except:
        pass

    # Собираем статистику

    # 1. Всего пользователей
    total_users_result = await session.execute(select(func.count()).select_from(User))
    total_users = total_users_result.scalar()

    # 2. Активные за 24 часа
    day_ago = datetime.utcnow() - timedelta(hours=24)
    active_24h_result = await session.execute(
        select(func.count(distinct(User.id)))
        .select_from(User)
        .where(User.last_active_date >= date.today())
    )
    active_24h = active_24h_result.scalar()

    # 3. Активные за 7 дней
    week_ago = date.today() - timedelta(days=7)
    active_7d_result = await session.execute(
        select(func.count(distinct(User.id)))
        .select_from(User)
        .where(User.last_active_date >= week_ago)
    )
    active_7d = active_7d_result.scalar()

    # 4. Новые за 24 часа
    new_24h_result = await session.execute(
        select(func.count())
        .select_from(User)
        .where(User.created_at >= day_ago)
    )
    new_24h = new_24h_result.scalar()

    # 5. Всего викторин пройдено
    total_quizzes_result = await session.execute(
        select(func.count())
        .select_from(QuizSession)
        .where(QuizSession.completed_at.isnot(None))
    )
    total_quizzes = total_quizzes_result.scalar()

    # 6. Викторин за 24 часа
    quizzes_24h_result = await session.execute(
        select(func.count())
        .select_from(QuizSession)
        .where(
            QuizSession.completed_at.isnot(None),
            QuizSession.completed_at >= day_ago
        )
    )
    quizzes_24h = quizzes_24h_result.scalar()

    # 7. Средняя длительность викторины (в секундах)
    avg_duration_result = await session.execute(
        select(func.avg(
            func.extract('epoch', QuizSession.completed_at - QuizSession.started_at)
        ))
        .select_from(QuizSession)
        .where(QuizSession.completed_at.isnot(None))
    )
    avg_duration_seconds = avg_duration_result.scalar() or 0
    avg_duration_min = int(avg_duration_seconds / 60)

    # 8. Средний результат викторин
    avg_result_result = await session.execute(
        select(func.avg(QuizSession.correct_answers * 100.0 / QuizSession.total_questions))
        .select_from(QuizSession)
        .where(QuizSession.completed_at.isnot(None))
    )
    avg_result = avg_result_result.scalar() or 0

    # 9. Распределение по уровням
    levels_result = await session.execute(
        select(User.level, func.count())
        .select_from(User)
        .group_by(User.level)
    )
    levels = levels_result.all()

    # Формируем текст
    admin_text = "👨‍💼 <b>АДМИН-ПАНЕЛЬ</b>\n\n"

    admin_text += "📊 <b>Пользователи:</b>\n"
    admin_text += f"├─ Всего: <b>{total_users}</b>\n"
    admin_text += f"├─ 🟢 Активных за 24ч: <b>{active_24h}</b>\n"
    admin_text += f"├─ 📅 Активных за 7 дней: <b>{active_7d}</b>\n"
    admin_text += f"└─ 🆕 Новых за 24ч: <b>{new_24h}</b>\n\n"

    admin_text += "🏆 <b>Викторины:</b>\n"
    admin_text += f"├─ Всего пройдено: <b>{total_quizzes}</b>\n"
    admin_text += f"├─ За 24 часа: <b>{quizzes_24h}</b>\n"
    admin_text += f"├─ Средняя длительность: <b>{avg_duration_min} мин</b>\n"
    admin_text += f"└─ Средний результат: <b>{avg_result:.1f}%</b>\n\n"

    admin_text += "📚 <b>По уровням:</b>\n"
    for level, count in levels:
        if level:
            percentage = (count / total_users * 100) if total_users > 0 else 0
            admin_text += f"├─ {level.value}: <b>{count}</b> ({percentage:.0f}%)\n"

    admin_text += "\n━━━━━━━━━━━━━━━━━\n"
    admin_text += "Команды:\n"
    admin_text += "/admin - эта панель\n"
    admin_text += "/admin_users - топ пользователей\n"
    admin_text += "/admin_stats - детальная статистика\n"

    await message.answer(admin_text)


@router.message(Command("admin_users"))
async def admin_users(message: Message, session: AsyncSession):
    """Список топ пользователей"""
    if not is_admin(message.from_user.id):
        return

    try:
        await message.delete()
    except:
        pass

    # Получаем топ-20 пользователей по streak
    result = await session.execute(
        select(User)
        .order_by(User.streak_days.desc(), User.quizzes_passed.desc())
        .limit(20)
    )
    users = result.scalars().all()

    text = "👥 <b>ТОП-20 АКТИВНЫХ ПОЛЬЗОВАТЕЛЕЙ</b>\n\n"

    for i, user in enumerate(users, 1):
        username = user.username or "без username"
        streak = user.streak_days or 0
        quizzes = user.quizzes_passed or 0
        words = user.words_learned or 0

        emoji = "🏆" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📍"

        text += f"{emoji} <b>#{i}</b> @{username}\n"
        text += f"   🔥 Стрик: {streak} дней | 🏆 Викторин: {quizzes} | 📚 Слов: {words}\n\n"

    await message.answer(text)


@router.message(Command("admin_stats"))
async def admin_detailed_stats(message: Message, session: AsyncSession):
    """Детальная статистика"""
    if not is_admin(message.from_user.id):
        return

    try:
        await message.delete()
    except:
        pass

    # 1. Самые сложные слова (топ-10)
    difficult_words_result = await session.execute(
        select(Word.word_de, Word.article, Word.translation_ru, Word.times_shown, Word.times_correct)
        .select_from(Word)
        .where(Word.times_shown >= 10)  # Показано хотя бы 10 раз
        .order_by((Word.times_correct * 100.0 / Word.times_shown).asc())
        .limit(10)
    )
    difficult_words = difficult_words_result.all()

    # 2. Retention (удержание)
    total_users_result = await session.execute(select(func.count()).select_from(User))
    total_users = total_users_result.scalar()

    # Пользователи с хотя бы одной викториной
    users_with_quiz_result = await session.execute(
        select(func.count(distinct(QuizSession.user_id)))
        .select_from(QuizSession)
        .where(QuizSession.completed_at.isnot(None))
    )
    users_with_quiz = users_with_quiz_result.scalar()

    # Пользователи со стриком >= 3
    users_streak_3_result = await session.execute(
        select(func.count())
        .select_from(User)
        .where(User.streak_days >= 3)
    )
    users_streak_3 = users_streak_3_result.scalar()

    # Пользователи со стриком >= 7
    users_streak_7_result = await session.execute(
        select(func.count())
        .select_from(User)
        .where(User.streak_days >= 7)
    )
    users_streak_7 = users_streak_7_result.scalar()

    # Формируем текст
    text = "📊 <b>ДЕТАЛЬНАЯ СТАТИСТИКА</b>\n\n"

    text += "🎯 <b>Engagement (вовлечённость):</b>\n"
    if total_users > 0:
        quiz_rate = (users_with_quiz / total_users * 100)
        streak3_rate = (users_streak_3 / total_users * 100)
        streak7_rate = (users_streak_7 / total_users * 100)

        text += f"├─ Прошли хотя бы 1 викторину: <b>{users_with_quiz}</b> ({quiz_rate:.1f}%)\n"
        text += f"├─ Стрик >= 3 дней: <b>{users_streak_3}</b> ({streak3_rate:.1f}%)\n"
        text += f"└─ Стрик >= 7 дней: <b>{users_streak_7}</b> ({streak7_rate:.1f}%)\n\n"

    text += "❌ <b>Самые сложные слова:</b>\n"
    for word_de, article, translation, shown, correct in difficult_words[:5]:
        word_display = f"{article} {word_de}" if article and article != '-' else word_de
        success_rate = (correct / shown * 100) if shown > 0 else 0
        text += f"├─ {word_display} ({translation})\n"
        text += f"│  Показано: {shown} раз | Правильно: {success_rate:.0f}%\n"

    await message.answer(text)


@router.message(Command("broadcast"))
async def admin_broadcast_start(message: Message):
    """Начало рассылки (заглушка)"""
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "📢 <b>Рассылка</b>\n\n"
        "Функция будет добавлена позже.\n"
        "Сейчас можно рассылать вручную через бота."
    )