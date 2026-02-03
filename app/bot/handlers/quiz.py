import random
import asyncio
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aiogram.filters import Command

from app.database.models import TranslationMode
from app.bot.states import QuizStates
from app.bot.keyboards import get_answer_keyboard, get_results_keyboard, get_main_menu_keyboard, get_level_keyboard, \
    get_translation_mode_keyboard
from app.database.models import User, QuizSession, QuizQuestion, Word, CEFRLevel
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.services.quiz_service import generate_question, update_word_progress, get_user_progress_stats
from datetime import date, timedelta

router = Router()


async def delete_messages_fast(bot, chat_id: int, start_id: int, end_id: int):
    """
    Быстрое удаление сообщений параллельно
    """
    tasks = []
    for msg_id in range(start_id, end_id):
        tasks.append(bot.delete_message(chat_id=chat_id, message_id=msg_id))

    # Удаляем все сообщения одновременно
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Логируем результаты
    deleted = sum(1 for r in results if not isinstance(r, Exception))
    print(f"   🧹 Удалено {deleted}/{len(tasks)} сообщений")


async def ensure_anchor(message: Message, session: AsyncSession, user: User, emoji: str = "🏠"):
    """
    Создаёт новый якорь БЕЗ удаления старого
    Старый якорь удалится позже вместе с остальными сообщениями

    ЛОГИКА:
    1. Создаём НОВЫЙ якорь (чат никогда не пустой!)
    2. Возвращаем ID старого якоря для удаления
    """
    old_anchor_id = user.anchor_message_id

    # Создаём новый якорь СРАЗУ (чтобы чат не был пустым)
    try:
        sent = await message.answer(emoji, reply_markup=get_main_menu_keyboard())
        new_anchor_id = sent.message_id

        # Обновляем ID якоря в базе
        user.anchor_message_id = new_anchor_id
        await session.commit()

        print(f"   ✨ Создан новый якорь {new_anchor_id}")

        # Возвращаем ID старого якоря для удаления
        return old_anchor_id, new_anchor_id
    except Exception as e:
        print(f"   ❌ Ошибка создания якоря: {e}")
        return old_anchor_id, None


async def cleanup_messages(message: Message, anchor_id: int, last_content_id: int):
    """
    Удаляет все сообщения между якорем и последним контентом
    """
    print(f"🧹 CLEANUP: Удаляю сообщения от {anchor_id + 1} до {last_content_id}")
    print(f"   Якорь ID: {anchor_id}")
    print(f"   Последний контент ID: {last_content_id}")
    print(f"   Всего удалить: {last_content_id - anchor_id - 1} сообщений")

    deleted_count = 0
    for msg_id in range(anchor_id + 1, last_content_id):
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=msg_id
            )
            deleted_count += 1
            print(f"   ✅ Удалено сообщение {msg_id}")
        except Exception as e:
            print(f"   ❌ Не удалось удалить {msg_id}: {e}")

    print(f"🧹 CLEANUP завершён: удалено {deleted_count} сообщений")


async def update_user_activity(session: AsyncSession, user_id: int):
    user = await session.get(User, user_id)
    today = date.today()
    if user.last_active_date == today:
        return
    elif user.last_active_date == today - timedelta(days=1):
        user.streak_days += 1
    else:
        user.streak_days = 1
    user.last_active_date = today
    await session.commit()


def get_next_question_keyboard() -> InlineKeyboardMarkup:
    """Кнопка 'Дальше' для перехода к следующему вопросу"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Дальше →", callback_data="next_question")]
        ]
    )


@router.message(F.text == "📚 Учить слова")
async def start_quiz(message: Message, state: FSMContext, session: AsyncSession):
    """Запуск викторины"""
    user_id = message.from_user.id

    # Получаем пользователя и его уровень
    user = await session.get(User, user_id)

    if not user or not user.level:
        await message.answer(
            "⚠️ Сначала выбери свой уровень с помощью команды /start"
        )
        return

    # Создаём новую сессию
    quiz_session = QuizSession(
        user_id=user_id,
        level=user.level,
        translation_mode=user.translation_mode,
        total_questions=25,
        correct_answers=0,
    )

    session.add(quiz_session)
    await session.flush()
    await session.commit()

    # Генерируем первый вопрос с учётом SRS
    try:
        question = await generate_question(
            level=user.level.value,
            session=session,
            user_id=user_id,
            exclude_ids=[],
            mode=user.translation_mode
        )
    except Exception as e:
        print(f"❌ Ошибка генерации вопроса: {e}")
        await message.answer(
            "❌ Произошла ошибка при подготовке викторины.\n"
            "Попробуйте ещё раз через /start"
        )
        return

    if not question:
        await message.answer(
            "❌ К сожалению, для этого уровня пока нет слов.\n"
            "Попробуй выбрать другой уровень."
        )
        return

    # Сохраняем данные в state
    await state.update_data(
        session_id=quiz_session.id,
        current_question=1,
        total_questions=25,
        correct_answers=0,
        errors=[],
        correct_word_id=question['correct_word'].id,
        used_word_ids=[question['correct_word'].id]
    )

    # Формируем текст вопроса
    word = question['correct_word']
    mode = user.translation_mode

    if mode.value == "ru_to_de":
        question_text = (
            f"Вопрос 1/25\n\n"
            f"🏳️‍🌈 <b>{word.translation_ru.capitalize()}</b>\n\n"
            f"📝 {word.example_ru}\n\n"
            f"Выбери правильное слово:"
        )
    else:
        word_display = word.word_de
        if word.article and word.article != '-':
            word_display = f"{word.article} {word.word_de}"

        question_text = (
            f"📝 Вопрос 1/25\n\n"
            f"🇩🇪 <b>{word_display}</b>\n\n"
            f"📝 {word.example_de}\n\n"
            f"Выбери правильный перевод:"
        )

    # Удаляем команду пользователя
    try:
        await message.delete()
    except:
        pass

    # Создаём новый якорь СРАЗУ
    old_anchor_id, new_anchor_id = await ensure_anchor(message, session, user, emoji="📚")

    # Удаляем всё старое параллельно
    if old_anchor_id:
        current_msg_id = message.message_id
        await delete_messages_fast(message.bot, message.chat.id, old_anchor_id, current_msg_id)

    # Отправляем первый вопрос
    await message.answer(
        question_text,
        reply_markup=get_answer_keyboard(question['options'])
    )

    await state.set_state(QuizStates.answering)


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
        # Получаем статистику прогресса по словам для текущего уровня
        try:
            progress = await get_user_progress_stats(user_id, user.level.value, session)
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
        stats_text = f"📊 <b>Статистика: Уровень {user.level.value}</b>\n\n"

        # Блок 1: Прогресс по словам
        stats_text += "📚 <b>Прогресс по словам:</b>\n"

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


@router.callback_query(F.data.startswith("answer_"), QuizStates.answering)
async def process_answer(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await update_user_activity(session, callback.from_user.id)

    # Обновляем закрепленное сообщение (якорь) с прогрессом, только если оно есть
    anchor_id = (await state.get_data()).get("anchor_message_id")
    if anchor_id:
        user = await session.get(User, callback.from_user.id)
        try:
            await callback.message.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=anchor_id,
                text=f"🔥 Стрик: {user.streak_days} дней\n"
                     f"📝 Выучено слов: {user.words_learned}\n"
                     f"🏆 Викторин: {user.quizzes_passed}\n"
                     f"✅ Правильных ответов: {user.success_rate}%\n"
                     f"🎯 Уровень: {user.level}",
                parse_mode="HTML"
            )
        except Exception:
            pass

    """Обработка ответа пользователя"""
    # Получаем ID выбранного слова
    selected_word_id = int(callback.data.split("_")[1])

    # Получаем данные из state
    data = await state.get_data()
    correct_word_id = data['correct_word_id']
    session_id = data['session_id']
    current_question = data['current_question']
    total_questions = data['total_questions']
    correct_answers = data['correct_answers']
    errors = data['errors']
    used_word_ids = data.get('used_word_ids', [])

    # Получаем правильное слово из БД
    correct_word = await session.get(Word, correct_word_id)

    # Проверяем правильность ответа
    is_correct = (selected_word_id == correct_word_id)

    # Сохраняем результат в БД
    session_item = QuizQuestion(
        session_id=session_id,
        word_id=correct_word_id,
        is_correct=is_correct,
        answered_at=datetime.utcnow()
    )
    session.add(session_item)
    await session.commit()

    # Обновляем прогресс пользователя по слову (SRS)
    try:
        await update_word_progress(
            user_id=callback.from_user.id,
            word_id=correct_word_id,
            is_correct=is_correct,
            session=session
        )
    except Exception as e:
        print(f"⚠️ Ошибка обновления прогресса: {e}")

    # Формируем правильный ответ для показа
    word_display = correct_word.word_de
    if correct_word.article and correct_word.article != '-':
        word_display = f"{correct_word.article} {correct_word.word_de}"

    # Получаем режим пользователя
    user = await session.get(User, callback.from_user.id)
    mode = user.translation_mode

    # Обновляем счётчик правильных ответов
    # Обновляем счётчик правильных ответов
    if is_correct:
        correct_answers += 1
        if mode.value == "ru_to_de":
            response_text = (
                f"✅ <b>Правильно!</b>\n\n"
                f"🏳️‍🌈 <b>{correct_word.translation_ru.capitalize()}</b> = 🇩🇪 <b>{word_display}</b>\n\n"
                f"🇩🇪 {correct_word.example_de}\n\n"
                f"🏳️‍🌈 {correct_word.example_ru}"
            )
        else:
            response_text = (
                f"✅ <b>Правильно!</b>\n\n"
                f"🇩🇪 <b>{word_display}</b> = 🏳️‍🌈 <b>{correct_word.translation_ru.capitalize()}</b>\n\n"
                f"🇩🇪 {correct_word.example_de}\n\n"
                f"🏳️‍🌈 {correct_word.example_ru}"
            )
    else:
        if mode.value == "ru_to_de":
            response_text = (
                f"❌ <b>Неправильно!</b>\n\n"
                f"Правильный ответ:\n\n"
                f"🏳️‍🌈 <b>{correct_word.translation_ru.capitalize()}</b> = 🇩🇪 <b>{word_display}</b>\n\n"
                f"🇩🇪 {correct_word.example_de}\n\n"
                f"🏳️‍🌈 {correct_word.example_ru}"
            )
        else:
            response_text = (
                f"❌ <b>Неправильно!</b>\n\n"
                f"Правильный ответ:\n\n"
                f"🇩🇪 <b>{word_display}</b> = 🏳️‍🌈 <b>{correct_word.translation_ru.capitalize()}</b>\n\n"
                f"🇩🇪 {correct_word.example_de}\n\n"
                f"🏳️‍🌈 {correct_word.example_ru}"
            )
        errors.append(correct_word_id)

    await callback.message.edit_text(
        response_text,
        reply_markup=get_next_question_keyboard()
    )

    # Обновляем state с новыми значениями
    await state.update_data(
        correct_answers=correct_answers,
        errors=errors
    )


@router.callback_query(F.data == "next_question", QuizStates.answering)
async def show_next_question(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()
    """Показ следующего вопроса"""
    # Получаем данные из state
    data = await state.get_data()
    current_question = data['current_question']
    total_questions = data['total_questions']
    used_word_ids = data.get('used_word_ids', [])

    # Генерируем следующий вопрос
    current_question += 1

    # Проверяем, не закончилась ли викторина
    if current_question > total_questions:
        # Викторина завершена - показываем результаты
        session_id = data['session_id']
        correct_answers = data['correct_answers']
        errors = data.get('errors', [])
        used_word_ids = data.get('used_word_ids', [])

        user = await session.get(User, callback.from_user.id)

        # Обновляем статистику пользователя
        user.quizzes_passed = (user.quizzes_passed or 0) + 1
        success_rate = int((correct_answers / total_questions) * 100)
        user.success_rate = success_rate

        unique_used = set(used_word_ids) if used_word_ids else set()
        user.words_learned = (user.words_learned or 0) + len(unique_used)

        await session.commit()

        # Обновляем якорь с прогрессом
        try:
            anchor_id = data.get("anchor_message_id")
            if anchor_id:
                await callback.message.bot.edit_message_text(
                    chat_id=callback.message.chat.id,
                    message_id=anchor_id,
                    text=(
                        f"🔥 Стрик: {user.streak_days} дней\n"
                        f"📝 Выучено слов: {user.words_learned}\n"
                        f"🏆 Викторин: {user.quizzes_passed}\n"
                        f"✅ Правильных ответов: {user.success_rate}%\n"
                        f"🎯 Уровень: {user.level}"
                    ),
                    parse_mode="HTML"
                )
        except:
            pass

        # Завершаем сессию в БД
        quiz_session = await session.get(QuizSession, session_id)
        quiz_session.correct_answers = correct_answers
        quiz_session.completed_at = datetime.utcnow()
        await session.commit()

        # Получаем детальную статистику
        result_items = await session.execute(
            select(QuizQuestion, Word)
            .join(Word, QuizQuestion.word_id == Word.id)
            .where(QuizQuestion.session_id == session_id)
            .order_by(QuizQuestion.answered_at)
        )
        items = result_items.all()

        # Формируем список правильных/неправильных
        details = []
        for item, word in items:
            word_display = word.word_de
            if word.article and word.article != '-':
                word_display = f"{word.article} {word.word_de}"

            icon = "✅" if item.is_correct else "❌"
            details.append(f"{icon} {word_display} — {word.translation_ru.capitalize()}")

        percentage = (correct_answers / total_questions) * 100
        result_text = (
                f"🎉 <b>Викторина завершена!</b>\n\n"
                f"📊 <b>Результаты:</b>\n"
                f"✅ Правильно: <b>{correct_answers}/{total_questions}</b>\n"
                f"📈 Процент: <b>{percentage:.1f}%</b>\n\n"
                f"📝 <b>Детали:</b>\n" + "\n".join(details)
        )

        if errors:
            result_text += f"\n\n❌ Ошибок: {len(errors)}"

        # Удаляем последнее сообщение
        try:
            await callback.message.delete()
        except:
            pass

        # Отправляем результаты
        await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text=result_text,
            reply_markup=get_results_keyboard(has_errors=bool(errors))
        )

        # Сохраняем ошибки для повтора
        saved_errors = errors.copy()
        await state.clear()
        await state.update_data(saved_errors=saved_errors)
        return

    user = await session.get(User, callback.from_user.id)

    # Проверяем, это повтор ошибок или обычная викторина
    error_words = data.get('error_words', [])

    if error_words:
        # Режим повтора ошибок - берём следующее слово из списка
        current_error_index = data.get('current_error_index', 0) + 1

        if current_error_index >= len(error_words):
            # Ошибки закончились (не должно произойти, но на всякий случай)
            await callback.message.answer("❌ Не удалось загрузить следующий вопрос.")
            await state.clear()
            await callback.answer()
            return

        # Получаем слово из списка ошибок
        next_word_id = error_words[current_error_index]
        next_word = await session.get(Word, next_word_id)

        # Генерируем дистракторы
        from app.services.quiz_service import get_distractors
        distractors = await get_distractors(next_word, session)

        if len(distractors) < 3:
            result = await session.execute(
                select(Word).where(
                    Word.level == user.level,
                    Word.id != next_word_id,
                    Word.id.not_in([d.id for d in distractors])
                )
            )
            all_words = result.scalars().all()
            if all_words:
                needed = min(3 - len(distractors), len(all_words))
                distractors.extend(random.sample(all_words, needed))

        # Формируем варианты ответов в зависимости от режима
        user = await session.get(User, callback.from_user.id)
        mode = user.translation_mode

        if mode.value == "ru_to_de":
            # RU→DE: показываем немецкие слова
            options = []
            word_display = next_word.word_de
            if next_word.article and next_word.article != '-':
                word_display = f"{next_word.article} {next_word.word_de}"
            options.append((next_word.id, word_display))

            for d in distractors[:3]:
                distractor_display = d.word_de
                if d.article and d.article != '-':
                    distractor_display = f"{d.article} {d.word_de}"
                options.append((d.id, distractor_display))
        else:
            # DE→RU: показываем русские переводы
            options = [(next_word.id, next_word.translation_ru.capitalize())]
            options.extend([(d.id, d.translation_ru.capitalize()) for d in distractors[:3]])

        random.shuffle(options)

        question = {
            'correct_word': next_word,
            'options': options
        }

        # Обновляем индекс
        await state.update_data(current_error_index=current_error_index)
    else:
        # Обычная викторина - генерируем случайный вопрос
        question = None
        attempts = 0
        max_attempts = 10

        while attempts < max_attempts:
            try:
                question = await generate_question(
                    level=user.level.value,
                    session=session,
                    user_id=callback.from_user.id,
                    exclude_ids=used_word_ids,
                    mode=user.translation_mode
                )
            except Exception as e:
                print(f"❌ Ошибка генерации вопроса: {e}")
                question = None

            if question:
                break
            attempts += 1

        if not question:
            await callback.message.answer("❌ Не удалось сгенерировать следующий вопрос.")
            await state.clear()
            await callback.answer()
            return

    # Дальше код остаётся как был (добавляем в used_word_ids и т.д.)

    if not question:
        await callback.message.answer("❌ Не удалось сгенерировать следующий вопрос.")
        await state.clear()
        await callback.answer()
        return

    # Добавляем слово в список использованных
    used_word_ids.append(question['correct_word'].id)

    # Обновляем state
    await state.update_data(
        current_question=current_question,
        correct_word_id=question['correct_word'].id,
        used_word_ids=used_word_ids
    )

    # Формируем текст следующего вопроса
    # Формируем текст следующего вопроса в зависимости от режима
    word = question['correct_word']
    user = await session.get(User, callback.from_user.id)
    mode = user.translation_mode

    # Определяем total для отображения (error_words или total_questions)
    display_total = len(error_words) if error_words else total_questions

    if mode.value == "ru_to_de":
        # Режим RU→DE: показываем русский перевод + пример
        question_text = (
            f"Вопрос {current_question}/{display_total}\n\n"
            f"🏳️‍🌈 <b>{word.translation_ru.capitalize()}</b>\n\n"
            f"📝 {word.example_ru}\n\n"
            f"Выбери правильное слово:"
        )
    else:
        # Режим DE→RU: показываем немецкое слово
        word_display = word.word_de
        if word.article and word.article != '-':
            word_display = f"{word.article} {word.word_de}"

        question_text = (
            f"📚 Вопрос {current_question}/{display_total}\n\n"
            f"🇩🇪 <b>{word_display}</b>\n\n"
            f"📝 {word.example_de}\n\n"
            f"Выбери правильный перевод:"
        )

    # Редактируем сообщение с ответом, заменяя его на новый вопрос
    await callback.message.edit_text(
        question_text,
        reply_markup=get_answer_keyboard(question['options'])
    )


@router.callback_query(F.data == "repeat_errors")
async def repeat_errors(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Повтор ошибок из предыдущей сессии"""
    # Получаем данные из state
    data = await state.get_data()
    errors = data.get('saved_errors', [])

    if not errors:
        await callback.message.answer("✅ У тебя не было ошибок!")
        await callback.answer()
        return

    user_id = callback.from_user.id
    user = await session.get(User, user_id)

    # Создаём новую сессию для повтора
    quiz_session = QuizSession(
        user_id=user_id,
        level=user.level,
        translation_mode=user.translation_mode,
        total_questions=len(errors),  # ← ИСПРАВЛЕНО: количество ошибок, а не 25
        correct_answers=0,
    )

    session.add(quiz_session)
    await session.flush()
    await session.commit()

    # Генерируем первый вопрос из ошибок
    first_word_id = errors[0]
    first_word = await session.get(Word, first_word_id)

    # Генерируем дистракторы для первого слова
    from app.services.quiz_service import get_distractors
    distractors = await get_distractors(first_word, session)

    if len(distractors) < 3:
        # Дополняем дистракторами из того же уровня
        result = await session.execute(
            select(Word).where(
                Word.cefr == user.level,
                Word.id != first_word_id,
                Word.id.not_in([d.id for d in distractors])
            )
        )
        all_words = result.scalars().all()
        if all_words:
            needed = min(3 - len(distractors), len(all_words))
            distractors.extend(random.sample(all_words, needed))

    # Формируем варианты ответов в зависимости от режима
    mode = user.translation_mode

    if mode.value == "ru_to_de":
        # RU→DE: показываем немецкие слова
        options = []
        word_display = first_word.word_de
        if first_word.article and first_word.article != '-':
            word_display = f"{first_word.article} {first_word.word_de}"
        options.append((first_word.id, word_display))

        for d in distractors[:3]:
            distractor_display = d.word_de
            if d.article and d.article != '-':
                distractor_display = f"{d.article} {d.word_de}"
            options.append((d.id, distractor_display))
    else:
        # DE→RU: показываем русские переводы
        options = [(first_word.id, first_word.translation_ru.capitalize())]
        options.extend([(d.id, d.translation_ru.capitalize()) for d in distractors[:3]])

    random.shuffle(options)

    # Сохраняем данные в state
    await state.update_data(
        session_id=quiz_session.id,
        current_question=1,
        total_questions=len(errors),
        correct_answers=0,
        errors=[],
        correct_word_id=first_word.id,
        error_words=errors,
        current_error_index=0
    )

    # Формируем текст вопроса в зависимости от режима
    if mode.value == "ru_to_de":
        question_text = (
            f"🔄 Повтор ошибок\n\n"
            f"Вопрос 1/{len(errors)}\n\n"
            f"🏳️‍🌈 <b>{first_word.translation_ru.capitalize()}</b>\n\n"
            f"📝 {first_word.example_ru}\n\n"
            f"Выбери правильное слово:"
        )
    else:
        word_display = first_word.word_de
        if first_word.article and first_word.article != '-':
            word_display = f"{first_word.article} {first_word.word_de}"

        question_text = (
            f"🔄 <b>Повтор ошибок</b>\n"
            f"📝 Вопрос 1/{len(errors)}\n\n"
            f"🇩🇪 <b>{word_display}</b>\n\n"
            f"📝 {first_word.example_de}\n\n"
            f"Выбери правильный перевод:"
        )

    # Удаляем сообщение со статистикой
    await callback.message.delete()

    # Показываем первый вопрос
    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text=question_text,
        reply_markup=get_answer_keyboard(options)
    )

    await state.set_state(QuizStates.answering)
    await callback.answer()


@router.callback_query(F.data == "main_menu")
async def return_to_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    # Очищаем state
    await state.clear()

    # Удаляем сообщение со статистикой
    await callback.message.delete()

    # Показываем главное меню
    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text="🏠 <b>Главное меню</b>\n\nВыбери действие:",
        reply_markup=get_main_menu_keyboard()
    )

    await callback.answer()


@router.message(F.text == "📚 Учить слова")
async def start_quiz(message: Message, state: FSMContext, session: AsyncSession):
    """Запуск викторины"""
    user_id = message.from_user.id

    # Получаем пользователя и его уровень
    user = await session.get(User, user_id)

    if not user or not user.level:
        await message.answer(
            "⚠️ Сначала выбери свой уровень с помощью команды /start"
        )
        return

    # Создаём новую сессию
    quiz_session = QuizSession(
        user_id=user_id,
        level=user.level,
        translation_mode=user.translation_mode,
        total_questions=25,
        correct_answers=0,
    )

    session.add(quiz_session)
    await session.flush()
    await session.commit()

    # Генерируем первый вопрос с учётом SRS
    try:
        question = await generate_question(
            level=user.level.value,
            session=session,
            user_id=user_id,
            exclude_ids=[],
            mode=user.translation_mode
        )
    except Exception as e:
        print(f"❌ Ошибка генерации вопроса: {e}")
        question = None

    if not question:
        await message.answer(
            "❌ К сожалению, для этого уровня пока нет слов.\n"
            "Попробуй выбрать другой уровень."
        )
        return

    # Сохраняем данные в state
    await state.update_data(
        session_id=quiz_session.id,
        current_question=1,
        total_questions=25,
        correct_answers=0,
        errors=[],
        correct_word_id=question['correct_word'].id,
        used_word_ids=[question['correct_word'].id]
    )

    # Формируем текст вопроса
    word = question['correct_word']
    mode = user.translation_mode

    if mode.value == "ru_to_de":
        question_text = (
            f"📝 Вопрос 1/25\n\n"
            f"🏳️‍🌈 <b>{word.translation_ru.capitalize()}</b>\n\n"
            f"📝 {word.example_ru}\n\n"
            f"Выбери правильное слово:"
        )
    else:
        word_display = word.word_de
        if word.article and word.article != '-':
            word_display = f"{word.article} {word.word_de}"

        question_text = (
            f"📝 Вопрос 1/25\n\n"
            f"🇩🇪 <b>{word_display}</b>\n\n"
            f"📝 {word.example_de}\n\n"
            f"Выбери правильный перевод:"
        )

    # Удаляем команду пользователя
    try:
        await message.delete()
    except:
        pass

    # Создаём новый якорь СРАЗУ
    old_anchor_id, new_anchor_id = await ensure_anchor(message, session, user, emoji="📚")

    # Удаляем всё старое параллельно
    if old_anchor_id:
        current_msg_id = message.message_id
        await delete_messages_fast(message.bot, message.chat.id, old_anchor_id, current_msg_id)

    # Отправляем первый вопрос
    await message.answer(
        question_text,
        reply_markup=get_answer_keyboard(question['options'])
    )

    await state.set_state(QuizStates.answering)


@router.message(Command("settings"))
@router.message(F.text == "🦾 Настройки")
async def show_settings(message: Message, state: FSMContext, session: AsyncSession):
    """Показ настроек"""
    user_id = message.from_user.id
    user = await session.get(User, user_id)

    current_level = user.level.value if user and user.level else "не выбран"
    current_mode = user.translation_mode if user else "DE_TO_RU"

    if current_mode.value == "de_to_ru":
        mode_text = "🇩🇪→🏳️‍🌈 Немецкий → Русский"
    else:
        mode_text = "🏳️‍🌈→🇩🇪 Русский → Немецкий"

    settings_text = (
        f"⚙️ <b>Настройки</b>\n\n"
        f"📚 Уровень: <b>{current_level}</b>\n"
        f"🔄 Режим перевода: <b>{mode_text}</b>\n\n"
        f"Что хочешь изменить?"
    )

    buttons = [
        [InlineKeyboardButton(text="📚 Изменить уровень", callback_data="change_level")],
        [InlineKeyboardButton(text="🔄 Изменить режим перевода", callback_data="change_mode")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    # Удаляем команду пользователя
    try:
        await message.delete()
    except:
        pass

    # Создаём новый якорь СРАЗУ
    old_anchor_id, new_anchor_id = await ensure_anchor(message, session, user, emoji="🦾")

    # Удаляем всё старое параллельно
    if old_anchor_id:
        current_msg_id = message.message_id
        await delete_messages_fast(message.bot, message.chat.id, old_anchor_id, current_msg_id)

    # Отправляем настройки
    await message.answer(settings_text, reply_markup=keyboard)


@router.callback_query(F.data == "change_level")
async def settings_change_level(callback: CallbackQuery, state: FSMContext):
    """Переход к выбору уровня из настроек"""
    # Создаём клавиатуру с кнопкой "Назад"
    levels = list(CEFRLevel)
    buttons = [
        [
            InlineKeyboardButton(text=levels[0].value, callback_data=f"level_{levels[0].value}"),
            InlineKeyboardButton(text=levels[1].value, callback_data=f"level_{levels[1].value}")
        ],
        [
            InlineKeyboardButton(text=levels[2].value, callback_data=f"level_{levels[2].value}"),
            InlineKeyboardButton(text=levels[3].value, callback_data=f"level_{levels[3].value}")
        ],
        [
            InlineKeyboardButton(text=levels[4].value, callback_data=f"level_{levels[4].value}"),
            InlineKeyboardButton(text=levels[5].value, callback_data=f"level_{levels[5].value}")
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_settings")]  # ← ДОБАВИЛИ
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(
        "📚 <b>Выбери новый уровень:</b>",
        reply_markup=keyboard
    )
    await state.set_state(QuizStates.choosing_level)
    await callback.answer()


@router.callback_query(F.data == "change_mode")
async def settings_change_mode(callback: CallbackQuery, session: AsyncSession):
    """Переход к выбору режима перевода"""
    user_id = callback.from_user.id
    user = await session.get(User, user_id)
    current_mode = user.translation_mode if user else "DE_TO_RU"

    await callback.message.edit_text(
        "🔄 <b>Выбери режим перевода:</b>\n\n"
        "🇩🇪→🏳️‍🌈 <b>DE-RU</b> — Немецкое слово → Русский перевод\n"
        "🏳️‍🌈→🇩🇪 <b>RU-DE</b> — Русский перевод → Немецкое слово",
        reply_markup=get_translation_mode_keyboard(current_mode)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("mode_"))
async def set_translation_mode(callback: CallbackQuery, session: AsyncSession):
    """Установка режима перевода"""
    mode = callback.data[5:]
    user_id = callback.from_user.id

    # Обновляем режим
    user = await session.get(User, user_id)
    user.translation_mode = TranslationMode(mode)
    await session.commit()

    mode_text = "🇩🇪→🏳️‍🌈 Немецкий → Русский" if mode == "de_to_ru" else "🏳️‍🌈→🇩🇪 Русский → Немецкий"

    await callback.message.edit_text(
        f"✅ Режим перевода изменён!\n\n"
        f"Новый режим: <b>{mode_text}</b>"
    )

    await callback.answer()


@router.callback_query(F.data == "back_to_settings")
async def back_to_settings(callback: CallbackQuery, session: AsyncSession):
    """Возврат в меню настроек"""
    user_id = callback.from_user.id
    user = await session.get(User, user_id)

    current_level = user.level.value if user and user.level else "не выбран"
    current_mode = user.translation_mode if user else "DE_TO_RU"

    if current_mode.value == "de_to_ru":
        mode_text = "🇩🇪→🏳️‍🌈 Немецкий → Русский"
    else:
        mode_text = "🏳️‍🌈→🇩🇪 Русский → Немецкий"

    settings_text = (
        f"⚙️ <b>Настройки</b>\n\n"
        f"📚 Уровень: <b>{current_level}</b>\n"
        f"🔄 Режим перевода: <b>{mode_text}</b>\n\n"
        f"Что хочешь изменить?"
    )

    buttons = [
        [InlineKeyboardButton(text="📚 Изменить уровень", callback_data="change_level")],
        [InlineKeyboardButton(text="🔄 Изменить режим перевода", callback_data="change_mode")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(settings_text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("level_"), QuizStates.choosing_level)
async def change_level(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Смена уровня в настройках"""
    level = callback.data.split("_")[1]
    user_id = callback.from_user.id

    # Обновляем уровень пользователя
    user = await session.get(User, user_id)
    user.level = level
    await session.commit()

    # Удаляем сообщение с выбором уровня
    await callback.message.delete()

    # Показываем подтверждение и меню
    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text=f"✅ Уровень изменён на <b>{level}</b>!\n\nВыбери действие:",
        reply_markup=get_main_menu_keyboard()
    )

    await state.clear()
    await callback.answer()