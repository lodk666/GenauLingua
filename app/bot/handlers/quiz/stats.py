"""
Статистика и прогресс пользователя
Прогресс по словам, викторины, активность
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


async def delete_messages_fast(bot, chat_id: int, start_id: int, end_id: int):
    """Быстрое удаление сообщений параллельно"""
    tasks = []
    for msg_id in range(start_id, end_id):
        tasks.append(bot.delete_message(chat_id=chat_id, message_id=msg_id))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    deleted = sum(1 for r in results if not isinstance(r, Exception))
    print(f"   🧹 Удалено {deleted}/{len(tasks)} сообщений")


async def ensure_anchor(message: Message, session: AsyncSession, user: User, emoji: str = "🏠"):
    """Создаёт новый якорь БЕЗ удаления старого"""
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


# ============================================================================
# ГЛАВНОЕ МЕНЮ СТАТИСТИКИ
# ============================================================================

@router.message(Command("stats"))
@router.message(F.text == "📊 Статистика")
async def show_statistics(message: Message, state: FSMContext, session: AsyncSession):
    """Показ детальной статистики пользователя по текущему уровню"""
    user_id = message.from_user.id
    user = await session.get(User, user_id)

    # Удаляем команду/сообщение пользователя
    try:
        await message.delete()
    except:
        pass

    if not user or not user.level:
        stats_text = (
            "⚠️ <b>Сначала выбери уровень!</b>\n\n"
            "Используй команду /start чтобы начать."
        )
    else:
        # Получаем статистику прогресса по словам (все уровни)
        try:
            overall_progress = await get_user_progress_stats_all_levels(user_id, session)
        except Exception as e:
            print(f"⚠️ Ошибка получения общей статистики: {e}")
            overall_progress = {
                'total_words': 0,
                'seen_words': 0,
                'learned_words': 0,
                'struggling_words': 0,
                'new_words': 0
            }

        # Получаем статистику прогресса по словам для текущего уровня
        try:
            progress = await get_user_progress_stats(user_id, user.level, session)
        except Exception as e:
            print(f"⚠️ Ошибка получения статистики: {e}")
            progress = {
                'total_words': 0,
                'seen_words': 0,
                'learned_words': 0,
                'struggling_words': 0,
                'new_words': 0
            }

        # Получаем завершённые викторины для текущего уровня
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

        # Для детального показа берём только последние 5
        level_sessions = all_level_sessions[:5]

        # Формируем текст статистики
        stats_text = f"📊 <b>Статистика</b>\n"
        stats_text += f"🎯 Текущий уровень: <b>{user.level.value}</b>\n\n"

        # Блок 0: Вся статистика (все уровни)
        stats_text += "🌍 <b>Вся статистика (все уровни):</b>\n"

        overall_total = overall_progress['total_words']
        overall_learned = overall_progress['learned_words']
        overall_seen = overall_progress['seen_words']
        overall_struggling = overall_progress['struggling_words']
        overall_new = overall_progress['new_words']
        overall_in_progress = overall_seen - overall_learned

        if overall_total > 0:
            overall_learned_percent = (overall_learned / overall_total) * 100
            overall_progress_bar = create_progress_bar(overall_learned_percent)

            stats_text += f"Всего слов: <b>{overall_total}</b>\n"
            stats_text += f"{overall_progress_bar} {overall_learned_percent:.1f}%\n\n"
            stats_text += (
                f"├─ ✅ Выучено: <b>{overall_learned}</b> "
                f"({(overall_learned / overall_total * 100):.1f}%)\n"
            )
            stats_text += (
                f"├─ 🔄 В процессе: <b>{overall_in_progress}</b> "
                f"({(overall_in_progress / overall_total * 100):.1f}%)\n"
            )
            stats_text += (
                f"├─ ❌ Сложные: <b>{overall_struggling}</b> "
                f"({(overall_struggling / overall_total * 100):.1f}%)\n"
            )
            stats_text += (
                f"└─ 🆕 Новых: <b>{overall_new}</b> "
                f"({(overall_new / overall_total * 100):.1f}%)\n\n"
            )
        else:
            stats_text += "Слов в базе не найдено.\n\n"

        # Блок 1: Прогресс по словам (текущий уровень)
        stats_text += f"📚 <b>Прогресс по словам (уровень {user.level.value}):</b>\n"

        total = progress['total_words']
        learned = progress['learned_words']
        seen = progress['seen_words']
        struggling = progress['struggling_words']
        new = progress['new_words']
        in_progress = seen - learned  # Видел, но ещё не выучил

        if total > 0:
            learned_percent = (learned / total) * 100
            progress_bar = create_progress_bar(learned_percent)

            stats_text += f"Всего слов: <b>{total}</b>\n"
            stats_text += f"{progress_bar} {learned_percent:.1f}%\n\n"
            stats_text += f"├─ ✅ Выучено: <b>{learned}</b> ({(learned / total * 100):.1f}%)\n"
            stats_text += f"├─ 🔄 В процессе: <b>{in_progress}</b> ({(in_progress / total * 100):.1f}%)\n"
            stats_text += f"├─ ❌ Сложные: <b>{struggling}</b> ({(struggling / total * 100):.1f}%)\n"
            stats_text += f"└─ 🆕 Новых: <b>{new}</b> ({(new / total * 100):.1f}%)\n\n"
        else:
            stats_text += "Слов для этого уровня не найдено.\n\n"

        # Блок 2: Статистика викторин по уровню
        if all_level_sessions:
            stats_text += f"🏆 <b>Викторины (уровень {user.level.value}):</b>\n"

            total_quizzes = len(all_level_sessions)  # ← Все викторины
            total_questions_level = sum(s.total_questions for s in all_level_sessions)
            total_correct_level = sum(s.correct_answers for s in all_level_sessions)
            avg_percent = (total_correct_level / total_questions_level * 100) if total_questions_level > 0 else 0
            best_result = max(
                (s.correct_answers / s.total_questions * 100) for s in all_level_sessions) if all_level_sessions else 0

            stats_text += f"├─ Пройдено: <b>{total_quizzes}</b> викторин\n"
            stats_text += f"├─ Средний результат: <b>{avg_percent:.1f}%</b>\n"
            stats_text += f"└─ Лучший результат: <b>{best_result:.1f}%</b>\n\n"
        else:
            stats_text += f"🏆 <b>Викторины (уровень {user.level.value}):</b>\n"
            stats_text += "Ты ещё не проходил викторины на этом уровне.\n\n"

        # Блок 3: Общая активность
        stats_text += "🔥 <b>Активность:</b>\n"
        stats_text += f"└─ Стрик: <b>{user.streak_days}</b> дней подряд\n\n"

        # Блок 4: Последние викторины
        if level_sessions:
            stats_text += "━━━━━━━━━━━━━━━━━\n"
            stats_text += "<b>Последние викторины:</b>\n\n"

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

        # Добавляем пояснение
        stats_text += "\n━━━━━━━━━━━━━━━━━\n"
        stats_text += "💡 <b>Выучено</b> — 3 правильных ответа подряд по слову"

    # Создаём новый якорь СРАЗУ
    old_anchor_id, new_anchor_id = await ensure_anchor(message, session, user, emoji="📊")

    # Удаляем всё старое параллельно
    if old_anchor_id:
        current_msg_id = message.message_id
        await delete_messages_fast(message.bot, message.chat.id, old_anchor_id, current_msg_id)

    # Отправляем статистику
    await message.answer(stats_text)


def create_progress_bar(percent: float, length: int = 10) -> str:
    """Создаёт визуальный прогресс-бар"""
    filled = int((percent / 100) * length)
    empty = length - filled
    return f"[{'█' * filled}{'░' * empty}]"