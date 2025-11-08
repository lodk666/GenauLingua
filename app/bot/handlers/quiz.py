import random
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aiogram.filters import Command

from app.bot.states import QuizStates
from app.bot.keyboards import get_answer_keyboard, get_results_keyboard, get_main_menu_keyboard, get_level_keyboard, get_translation_mode_keyboard
from app.database.models import User, QuizSession, QuizQuestion, Word, CEFRLevel
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.services.quiz_service import generate_question

router = Router()

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

    # Генерируем первый вопрос
    question = await generate_question(user.level, session, mode=user.translation_mode)

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

    if mode == "RU_TO_DE":
        question_text = (
            f"📝 Вопрос 1/25\n\n"
            f"🇷🇺 <b>{word.translation_ru.capitalize()}</b>\n\n"
            f"Выбери правильное слово:"
        )
    else:
        word_display = word.word_de
        if word.article and word.article != '-':
            word_display = f"{word.article} {word.word_de}"

        question_text = (
            f"📝 Вопрос 1/25\n\n"
            f"🇩🇪 <b>{word_display}</b>\n\n"
            f"Выбери правильный перевод:"
        )

    # Удаляем команду пользователя
    try:
        await message.delete()
    except:
        pass

    # Удаляем все предыдущие сообщения
    try:
        for i in range(1, 8):
            try:
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=message.message_id - i
                )
            except:
                pass
    except:
        pass

    # Отправляем эмодзи с меню
    await message.answer("📚", reply_markup=get_main_menu_keyboard())

    # Отправляем первый вопрос
    await message.answer(
        question_text,
        reply_markup=get_answer_keyboard(question['options'])
    )

    await state.set_state(QuizStates.answering)

@router.message(Command("stats"))
@router.message(F.text == "📊 Статистика")
async def show_statistics(message: Message, state: FSMContext, session: AsyncSession):
    """Показ статистики пользователя"""
    user_id = message.from_user.id

    # Удаляем команду/сообщение пользователя
    try:
        await message.delete()
    except:
        pass

    # Удаляем предыдущие сообщения
    try:
        for i in range(1, 8):
            try:
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=message.message_id - i
                )
            except:
                pass
    except:
        pass

    # Получаем все завершённые сессии пользователя
    result = await session.execute(
        select(QuizSession)
        .where(
            QuizSession.user_id == user_id,
            QuizSession.completed_at.isnot(None)
        )
        .order_by(QuizSession.started_at.desc())
        .limit(10)
    )
    sessions = result.scalars().all()

    if not sessions:
        stats_text = (
            "📊 <b>Статистика</b>\n\n"
            "У тебя пока нет завершённых викторин.\n"
            "Начни учить слова! 📚"
        )
    else:
        stats_text = "📊 <b>Твоя статистика</b>\n\n"
        stats_text += f"Всего викторин: <b>{len(sessions)}</b>\n\n"

        total_questions = sum(s.total_questions for s in sessions)
        total_correct = sum(s.correct_answers for s in sessions)
        overall_percentage = (total_correct / total_questions * 100) if total_questions > 0 else 0

        stats_text += (
            f"📈 <b>Общий результат:</b>\n"
            f"✅ Правильно: {total_correct}/{total_questions}\n"
            f"📊 Процент: {overall_percentage:.1f}%\n\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"<b>Последние 10 викторин:</b>\n\n"
        )

        for i, s in enumerate(sessions, 1):
            percentage = (s.correct_answers / s.total_questions * 100) if s.total_questions > 0 else 0
            date_str = s.started_at.strftime("%d.%m.%Y %H:%M")

            if percentage >= 80:
                emoji = "🏆"
            elif percentage >= 60:
                emoji = "👍"
            else:
                emoji = "📝"

            stats_text += (
                f"{emoji} <b>#{i}</b> • {date_str}\n"
                f"   Уровень: {s.level.value}\n"
                f"   Результат: {s.correct_answers}/{s.total_questions} ({percentage:.0f}%)\n\n"
            )

    # Отправляем эмодзи с меню
    await message.answer("📊", reply_markup=get_main_menu_keyboard())

    # Отправляем статистику
    await message.answer(stats_text)

@router.callback_query(F.data.startswith("answer_"), QuizStates.answering)
async def process_answer(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()
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
        if mode == "RU_TO_DE":
            response_text = (
                f"✅ <b>Правильно!</b>\n\n"
                f"🇷🇺 <b>{correct_word.translation_ru.capitalize()}</b> = 🇩🇪 <b>{word_display}</b>\n\n"
                f"🇩🇪 {correct_word.example_de}\n\n"
                f"🇷🇺 {correct_word.example_ru}"
            )
        else:
            response_text = (
                f"✅ <b>Правильно!</b>\n\n"
                f"🇩🇪 <b>{word_display}</b> = 🇷🇺 <b>{correct_word.translation_ru.capitalize()}</b>\n\n"
                f"🇩🇪 {correct_word.example_de}\n\n"
                f"🇷🇺 {correct_word.example_ru}"
            )
    else:
        if mode == "RU_TO_DE":
            response_text = (
                f"❌ <b>Неправильно!</b>\n\n"
                f"Правильный ответ:\n\n"
                f"🇷🇺 <b>{correct_word.translation_ru.capitalize()}</b> = 🇩🇪 <b>{word_display}</b>\n\n"
                f"🇩🇪 {correct_word.example_de}\n\n"
                f"🇷🇺 {correct_word.example_ru}"
            )
        else:
            response_text = (
                f"❌ <b>Неправильно!</b>\n\n"
                f"Правильный ответ:\n\n"
                f"🇩🇪 <b>{word_display}</b> = 🇷🇺 <b>{correct_word.translation_ru.capitalize()}</b>\n\n"
                f"🇩🇪 {correct_word.example_de}\n\n"
                f"🇷🇺 {correct_word.example_ru}"
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

    # Проверяем, закончились ли вопросы
    if current_question >= total_questions:
        # Завершаем сессию
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

        # ПРОСТОЕ РЕШЕНИЕ:
            # 1. Удаляем последний ответ викторины
            try:
                await callback.message.delete()
            except:
                pass

            # 2. Удаляем все предыдущие сообщения
            try:
                for i in range(1, 8):
                    try:
                        await callback.bot.delete_message(
                            chat_id=callback.message.chat.id,
                            message_id=callback.message.message_id - i
                        )
                    except:
                        pass
            except:
                pass

            # 3. Отправляем галочку с меню
            await callback.bot.send_message(
                chat_id=callback.message.chat.id,
                text="✅",
                reply_markup=get_main_menu_keyboard()
            )

            # 4. Отправляем результаты
            await callback.bot.send_message(
                chat_id=callback.message.chat.id,
                text=result_text,
                reply_markup=get_results_keyboard(has_errors=bool(errors))
            )

            # Сохраняем ошибки
            saved_errors = errors.copy()
            await state.clear()
            await state.update_data(saved_errors=saved_errors)

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
        # ... (весь блок завершения остаётся как есть)
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
                    Word.cefr == user.level,
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

            if mode == "RU_TO_DE":
                # RU→DE: показываем немецкие слова
                options = []
                word_display = next_word.word_de
                if next_word.article and next_word.article != '-':
                    word_display = f"{next_word.article} {next_word.word_de}"
                options.append((next_word.id, word_display))

                for d in distractors[:3]:
                    distractor_display = d.lemma
                    if d.article and d.article != '-':
                        distractor_display = f"{d.article} {d.lemma}"
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
            question = await generate_question(user.level, session, exclude_ids=used_word_ids, mode=user.translation_mode)
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

    if mode == "RU_TO_DE":
        # Режим RU→DE: показываем русский перевод
        question_text = (
            f"📝 <b>Вопрос {current_question}/{total_questions}</b>\n\n"
            f"🇷🇺 <b>{word.translation_ru.capitalize()}</b>\n\n"
            f"Выбери правильное слово:"
        )
    else:
        # Режим DE→RU: показываем немецкое слово
        word_display = word.word_de
        if word.article and word.article != '-':
            word_display = f"{word.article} {word.word_de}"

        question_text = (
            f"📚 Вопрос {current_question}/{total_questions}\n\n"
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
        total_questions=25,
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

    if mode == "RU_TO_DE":
        # RU→DE: показываем немецкие слова
        options = []
        word_display = first_word.word_de
        if first_word.article and first_word.article != '-':
            word_display = f"{first_word.article} {first_word.word_de}"
        options.append((first_word.id, word_display))

        for d in distractors[:3]:
            distractor_display = d.lemma
            if d.article and d.article != '-':
                distractor_display = f"{d.article} {d.lemma}"
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
    if mode == "RU_TO_DE":
        question_text = (
            f"🔄 <b>Повтор ошибок</b>\n"
            f"📝 Вопрос 1/{len(errors)}\n\n"
            f"🇷🇺 <b>{first_word.translation_ru.capitalize()}</b>\n\n"
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

    # Генерируем первый вопрос
    question = await generate_question(user.level, session, mode=user.translation_mode)

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

    if mode == "RU_TO_DE":
        question_text = (
            f"📝 Вопрос 1/25\n\n"
            f"🇷🇺 <b>{word.translation_ru.capitalize()}</b>\n\n"
            f"Выбери правильное слово:"
        )
    else:
        word_display = word.word_de
        if word.article and word.article != '-':
            word_display = f"{word.article} {word.word_de}"

        question_text = (
            f"📝 Вопрос 1/25\n\n"
            f"🇩🇪 <b>{word_display}</b>\n\n"
            f"Выбери правильный перевод:"
        )

    # Удаляем команду пользователя
    try:
        await message.delete()
    except:
        pass

    # Удаляем все предыдущие сообщения
    try:
        for i in range(1, 8):
            try:
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=message.message_id - i
                )
            except:
                pass
    except:
        pass

    # Отправляем эмодзи с меню
    await message.answer("📚", reply_markup=get_main_menu_keyboard())

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

    mode_text = "🇩🇪→🇷🇺 Немецкий → Русский" if current_mode == "DE_TO_RU" else "🇷🇺→🇩🇪 Русский → Немецкий"

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

    # Удаляем все предыдущие сообщения
    try:
        for i in range(1, 8):
            try:
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=message.message_id - i
                )
            except:
                pass
    except:
        pass

    # Отправляем эмодзи с меню
    await message.answer("🦾", reply_markup=get_main_menu_keyboard())

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
        "🇩🇪→🇷🇺 <b>DE-RU</b> — Немецкое слово → Русский перевод\n"
        "🇷🇺→🇩🇪 <b>RU-DE</b> — Русский перевод → Немецкое слово",
        reply_markup=get_translation_mode_keyboard(current_mode)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("mode_"))
async def set_translation_mode(callback: CallbackQuery, session: AsyncSession):
    """Установка режима перевода"""
    mode = callback.data.split("_")[1]
    user_id = callback.from_user.id

    # Обновляем режим
    user = await session.get(User, user_id)
    user.translation_mode = "DE_TO_RU"
    await session.commit()

    mode_text = "🇩🇪→🇷🇺 Немецкий → Русский" if mode == "DE_TO_RU" else "🇷🇺→🇩🇪 Русский → Немецкий"

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

    mode_text = "🇩🇪→🇷🇺 Немецкий → Русский" if current_mode == "DE_TO_RU" else "🇷🇺→🇩🇪 Русский → Немецкий"

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