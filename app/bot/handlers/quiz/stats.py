"""
Статистика и прогресс пользователя
"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio

from app.database.models import User, QuizSession
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


async def delete_messages_fast(bot, chat_id: int, start_id: int, end_id: int):
    tasks = []
    for msg_id in range(start_id, end_id):
        tasks.append(bot.delete_message(chat_id=chat_id, message_id=msg_id))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    deleted = sum(1 for r in results if not isinstance(r, Exception))
    print(f"   🧹 Удалено {deleted}/{len(tasks)} сообщений")


async def ensure_anchor(message: Message, session: AsyncSession, user: User, emoji: str = "🏠"):
    from app.bot.keyboards import get_main_menu_keyboard
    old_anchor_id = user.anchor_message_id
    try:
        sent = await message.answer(emoji, reply_markup=get_main_menu_keyboard())
        new_anchor_id = sent.message_id
        user.anchor_message_id = new_anchor_id
        await session.commit()
        print(f"   ✨ Создан новый якорь {new_anchor_id}")
        return old_anchor_id, new_anchor_id
    except Exception as e:
        print(f"   ❌ Ошибка создания якоря: {e}")
        return old_anchor_id, None


@router.message(Command("stats"))
@router.message(F.text == "📊 Статистика")
async def show_statistics(message: Message, state: FSMContext, session: AsyncSession):
    user_id = message.from_user.id
    user = await session.get(User, user_id)

    try:
        await message.delete()
    except:
        pass

    if not user or not user.level:
        await message.answer("⚠️ Сначала выбери уровень — используй /start")
        return

    # Получаем данные
    try:
        overall = await get_user_progress_stats_all_levels(user_id, session)
    except:
        overall = {'total_words': 0, 'seen_words': 0, 'learned_words': 0, 'struggling_words': 0, 'new_words': 0}

    try:
        level_progress = await get_user_progress_stats(user_id, user.level, session)
    except:
        level_progress = {'total_words': 0, 'seen_words': 0, 'learned_words': 0, 'struggling_words': 0, 'new_words': 0}

    result = await session.execute(
        select(QuizSession)
        .where(
            QuizSession.user_id == user_id,
            QuizSession.level == user.level,
            QuizSession.completed_at.isnot(None)
        )
        .order_by(QuizSession.started_at.desc())
    )
    all_sessions = result.scalars().all()
    last_sessions = all_sessions[:5]

    mode = MODE_DICT.get(user.translation_mode.value, user.translation_mode.value)

    # ── Блок 1: Вся база ──
    o_total = overall['total_words']
    o_learned = overall['learned_words']
    o_in_progress = overall['seen_words'] - overall['learned_words']
    o_new = overall['new_words']

    stats_text = "📊 <b>Статистика</b>\n\n"

    stats_text += f"📚 <b>Вся база ({o_total} слов)</b>\n"
    stats_text += f"✅ Выучено: <b>{o_learned}</b>\n"
    stats_text += f"🔄 В процессе: <b>{o_in_progress}</b>\n"
    stats_text += f"🆕 Новых: <b>{o_new}</b>\n\n"

    # ── Блок 2: Текущий уровень + режим ──
    l_total = level_progress['total_words']
    l_learned = level_progress['learned_words']
    l_in_progress = level_progress['seen_words'] - level_progress['learned_words']
    l_struggling = level_progress['struggling_words']
    l_new = level_progress['new_words']

    stats_text += f"──────────────────\n"
    stats_text += f"🎯 <b>Уровень {user.level.value} · {mode}</b> ({l_total} слов)\n"
    stats_text += f"✅ Выучено: <b>{l_learned}</b>\n"
    stats_text += f"🔄 В процессе: <b>{l_in_progress}</b>\n"

    if l_struggling > 0:
        stats_text += f"❌ Сложные: <b>{l_struggling}</b>\n"

    stats_text += f"🆕 Новых: <b>{l_new}</b>\n\n"

    # ── Блок 3: Викторины ──
    stats_text += f"──────────────────\n"
    stats_text += f"🏆 <b>Викторины (уровень {user.level.value})</b>\n"

    if all_sessions:
        total_q = sum(s.total_questions for s in all_sessions)
        total_c = sum(s.correct_answers for s in all_sessions)
        avg = (total_c / total_q * 100) if total_q > 0 else 0
        best = max((s.correct_answers / s.total_questions * 100) for s in all_sessions)

        stats_text += f"Пройдено: <b>{len(all_sessions)}</b>\n"
        stats_text += f"Средний результат: <b>{avg:.1f}%</b>\n"
        stats_text += f"Лучший результат: <b>{best:.1f}%</b>\n\n"

        if last_sessions:
            stats_text += "<b>Последние викторины:</b>\n"
            for s in last_sessions:
                pct = (s.correct_answers / s.total_questions * 100) if s.total_questions > 0 else 0
                date_str = s.started_at.strftime("%d.%m %H:%M")
                emoji = "🏆" if pct >= 80 else "👍" if pct >= 60 else "📝"
                stats_text += f"{emoji} {date_str} · {s.correct_answers}/{s.total_questions} ({pct:.0f}%)\n"
        stats_text += "\n"
    else:
        stats_text += "Ещё не проходил викторины на этом уровне.\n\n"

    # ── Блок 4: Активность ──
    stats_text += f"──────────────────\n"
    stats_text += f"🔥 Стрик: <b>{user.streak_days}</b> дней подряд\n\n"
    stats_text += "💡 <b>Выучено</b> — 3 правильных ответа подряд по слову"

    # Якорь и отправка
    old_anchor_id, new_anchor_id = await ensure_anchor(message, session, user, emoji="📊")

    if old_anchor_id:
        current_msg_id = message.message_id
        await delete_messages_fast(message.bot, message.chat.id, old_anchor_id, current_msg_id)

    await message.answer(stats_text)