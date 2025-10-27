import random
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


from app.bot.states import QuizStates
from app.bot.keyboards import get_answer_keyboard, get_results_keyboard, get_main_menu_keyboard
from app.database.models import User, Session, SessionItem, MasterWord
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

    if not user or not user.selected_level:
        await message.answer(
            "⚠️ Сначала выбери свой уровень с помощью команды /start"
        )
        return

    # Создаём новую сессию
    quiz_session = Session(
        user_id=user_id,
        level=user.selected_level,
        total_questions=25,  # По умолчанию 25 вопросов
        correct_answers=0,
        created_at=datetime.utcnow()
    )

    session.add(quiz_session)
    await session.flush()
    await session.commit()

    # Генерируем первый вопрос
    question = await generate_question(user.selected_level, session)

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
        errors=[],  # Список ID неправильных слов для повтора
        correct_word_id=question['correct_word'].id,
        used_word_ids = [question['correct_word'].id]
    )

    # Формируем текст вопроса
    word = question['correct_word']
    word_display = word.lemma

    # Для существительных показываем артикль
    if word.article and word.article.value != '-':
        word_display = f"{word.article.value} {word.lemma}"

    question_text = (
        f"📝 Вопрос 1/25\n\n"
        f"🇩🇪 <b>{word_display}</b>\n\n"
        f"Выбери правильный перевод:"
    )

    try:
        await message.delete()
    except:
        pass  # Если не удалось удалить - не критично

        # Удаляем все предыдущие сообщения бота (меню, приветствия)
        # Telegram позволяет удалять только последние сообщения
    try:
        # Пытаемся удалить последние 10 сообщений
        for i in range(1, 11):
            try:
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=message.message_id - i
                )
            except:
                pass  # Если сообщение уже удалено или нельзя удалить - пропускаем
    except:
        pass

        # Удаляем сообщение пользователя
    try:
        await message.delete()
    except:
        pass  # Если сообщение уже удалено или нельзя удалить - пропускаем

    await message.answer(
        question_text,
        reply_markup=get_answer_keyboard(question['options'])
    )

    await state.set_state(QuizStates.answering)


@router.callback_query(F.data.startswith("answer_"), QuizStates.answering)
async def process_answer(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
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
    correct_word = await session.get(MasterWord, correct_word_id)

    # Проверяем правильность ответа
    is_correct = (selected_word_id == correct_word_id)

    # Сохраняем результат в БД
    session_item = SessionItem(
        session_id=session_id,
        word_id=correct_word_id,
        is_correct=is_correct,
        answered_at=datetime.utcnow()
    )
    session.add(session_item)
    await session.commit()

    # Формируем правильный ответ для показа
    word_display = correct_word.lemma
    if correct_word.article and correct_word.article.value != '-':
        word_display = f"{correct_word.article.value} {correct_word.lemma}"

    # Обновляем счётчик правильных ответов
    if is_correct:
        correct_answers += 1
        response_text = (
            f"✅ <b>Правильно!</b>\n\n"
            f"🇩🇪 {word_display} = {correct_word.translation_ru.capitalize()}"
        )
    else:
        response_text = (
            f"❌ <b>Нeправильно!</b>\n\n"
            f"Правильный ответ:\n"
            f"🇩🇪 {word_display} = <b>{correct_word.translation_ru.capitalize()}</b>"
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
        quiz_session = await session.get(Session, session_id)
        quiz_session.correct_answers = correct_answers
        quiz_session.finished_at = datetime.utcnow()
        await session.commit()

        # Получаем детальную статистику
        result_items = await session.execute(
            select(SessionItem, MasterWord)
            .join(MasterWord, SessionItem.word_id == MasterWord.id)
            .where(SessionItem.session_id == session_id)
            .order_by(SessionItem.answered_at)
        )
        items = result_items.all()

        # Формируем список правильных/неправильных
        details = []
        for item, word in items:
            word_display = word.lemma
            if word.article and word.article.value != '-':
                word_display = f"{word.article.value} {word.lemma}"

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

        # Удаляем сообщение с ответом на последний вопрос
        await callback.message.delete()

        # Показываем результаты
        await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text=result_text,
            reply_markup=get_results_keyboard(has_errors=bool(errors))
        )

        # Сохраняем ошибки перед очисткой state
        saved_errors = errors.copy()
        await state.clear()

        # Возвращаем сохранённые ошибки для кнопки "Повторить"
        await state.update_data(saved_errors=saved_errors)

    await callback.answer()


@router.callback_query(F.data == "next_question", QuizStates.answering)
async def show_next_question(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
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
        next_word = await session.get(MasterWord, next_word_id)

        # Генерируем дистракторы
        from app.services.quiz_service import get_distractors
        distractors = await get_distractors(next_word, session)

        if len(distractors) < 3:
            result = await session.execute(
                select(MasterWord).where(
                    MasterWord.cefr == user.selected_level,
                    MasterWord.id != next_word_id,
                    MasterWord.id.not_in([d.id for d in distractors])
                )
            )
            all_words = result.scalars().all()
            if all_words:
                needed = min(3 - len(distractors), len(all_words))
                distractors.extend(random.sample(all_words, needed))

        # Формируем варианты ответов
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
            question = await generate_question(user.selected_level, session, exclude_ids=used_word_ids)
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
    word = question['correct_word']
    word_display = word.lemma

    if word.article and word.article.value != '-':
        word_display = f"{word.article.value} {word.lemma}"

    question_text = (
        f"📝 <b>Вопрос {current_question}/{total_questions}</b>\n\n"
        f"🇩🇪 <b>{word_display}</b>\n\n"
        f"Выбери правильный перевод:"
    )

    # Редактируем сообщение с ответом, заменяя его на новый вопрос
    await callback.message.edit_text(
        question_text,
        reply_markup=get_answer_keyboard(question['options'])
    )

    await callback.answer()


@router.callback_query(F.data == "repeat_errors")
async def repeat_errors(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Повтор ошибок из предыдущей сессии"""
    # Получаем данные из state
    data = await state.get_data()
    errors = data.get('saved_errors', [])  # ← ИЗМЕНЕНО: ищем saved_errors

    if not errors:
        await callback.message.answer("✅ У тебя не было ошибок!")
        await callback.answer()
        return

    user_id = callback.from_user.id
    user = await session.get(User, user_id)

    # Создаём новую сессию для повтора
    quiz_session = Session(
        user_id=user_id,
        level=user.selected_level,
        total_questions=len(errors),
        correct_answers=0,
        created_at=datetime.utcnow()
    )

    session.add(quiz_session)
    await session.flush()
    await session.commit()

    # Генерируем первый вопрос из ошибок
    first_word_id = errors[0]
    first_word = await session.get(MasterWord, first_word_id)

    # Генерируем дистракторы для первого слова
    from app.services.quiz_service import get_distractors
    distractors = await get_distractors(first_word, session)

    if len(distractors) < 3:
        # Дополняем дистракторами из того же уровня
        result = await session.execute(
            select(MasterWord).where(
                MasterWord.cefr == user.selected_level,
                MasterWord.id != first_word_id,
                MasterWord.id.not_in([d.id for d in distractors])
            )
        )
        all_words = result.scalars().all()
        if all_words:
            needed = min(3 - len(distractors), len(all_words))
            distractors.extend(random.sample(all_words, needed))

    # Формируем варианты ответов
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

    # Формируем текст вопроса
    word_display = first_word.lemma
    if first_word.article and first_word.article.value != '-':
        word_display = f"{first_word.article.value} {first_word.lemma}"

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