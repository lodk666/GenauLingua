from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.states import QuizStates
from app.bot.keyboards import get_answer_keyboard, get_results_keyboard
from app.database.models import User, Session, SessionItem
from app.services.quiz_service import generate_question

router = Router()


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
        correct_word_id=question['correct_word'].id
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

    # Обновляем счётчик правильных ответов
    if is_correct:
        correct_answers += 1
        response_text = "✅ Правильно!"
    else:
        response_text = "❌ Неправильно!"
        errors.append(correct_word_id)

    await callback.message.edit_text(
        f"{callback.message.text}\n\n{response_text}"
    )

    # Проверяем, закончились ли вопросы
    if current_question >= total_questions:
        # Завершаем сессию
        quiz_session = await session.get(Session, session_id)
        quiz_session.correct_answers = correct_answers
        quiz_session.finished_at = datetime.utcnow()
        await session.commit()

        # Показываем результаты
        percentage = (correct_answers / total_questions) * 100
        result_text = (
            f"🎉 Викторина завершена!\n\n"
            f"📊 Результаты:\n"
            f"✅ Правильно: {correct_answers}/{total_questions}\n"
            f"📈 Процент: {percentage:.1f}%\n"
        )

        if errors:
            result_text += f"\n❌ Ошибок: {len(errors)}"

        await callback.message.answer(
            result_text,
            reply_markup=get_results_keyboard(has_errors=bool(errors))
        )

        await state.clear()
        return

    # Генерируем следующий вопрос
    current_question += 1
    user = await session.get(User, callback.from_user.id)
    question = await generate_question(user.selected_level, session)

    if not question:
        await callback.message.answer("❌ Не удалось сгенерировать следующий вопрос.")
        await state.clear()
        return

    # Обновляем state
    await state.update_data(
        current_question=current_question,
        correct_answers=correct_answers,
        errors=errors,
        correct_word_id=question['correct_word'].id
    )

    # Формируем текст следующего вопроса
    word = question['correct_word']
    word_display = word.lemma

    if word.article and word.article.value != '-':
        word_display = f"{word.article.value} {word.lemma}"

    question_text = (
        f"📝 Вопрос {current_question}/{total_questions}\n\n"
        f"🇩🇪 <b>{word_display}</b>\n\n"
        f"Выбери правильный перевод:"
    )

    await callback.message.answer(
        question_text,
        reply_markup=get_answer_keyboard(question['options'])
    )

    await callback.answer()