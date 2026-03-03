"""
Игровая логика викторины с поддержкой локализации

ИСПРАВЛЕНИЯ:
1. ✅ words_learned теперь считается из UserWord (уникальные выученные слова)
2. ✅ success_rate теперь средний процент по всем викторинам
3. ✅ Добавлены комментарии с пометками FIXED
"""

import random
import asyncio
from datetime import datetime, date, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database.models import User, QuizSession, QuizQuestion, Word, TranslationMode, UserWord
from app.database.enums import CEFRLevel
from app.bot.states import QuizStates
from app.bot.keyboards import get_answer_keyboard, get_main_menu_keyboard
from app.locales import get_text
from app.services.quiz_service import (
    generate_question,
    update_word_progress,
    get_distractors,
)

router = Router()


async def delete_messages_fast(bot, chat_id: int, start_id: int, end_id: int):
    tasks = []
    for msg_id in range(start_id, end_id):
        tasks.append(bot.delete_message(chat_id=chat_id, message_id=msg_id))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    deleted = sum(1 for r in results if not isinstance(r, Exception))
    print(f"   🧹 Удалено {deleted}/{len(tasks)} сообщений")


async def ensure_anchor(message: Message, session: AsyncSession, user: User, emoji: str = "🏠"):
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


async def update_user_activity(session: AsyncSession, user_id: int):
    """Обновление стрика — только при завершении викторины"""
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


def get_next_question_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text("quiz_btn_next", lang), callback_data="next_question")]
        ]
    )


def get_results_keyboard(has_errors: bool, lang: str = "ru") -> InlineKeyboardMarkup:
    buttons = []
    if has_errors:
        buttons.append([
            InlineKeyboardButton(
                text=get_text("quiz_btn_repeat_errors", lang),
                callback_data="repeat_errors"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(F.text.in_(["📚 Учить слова", "📚 Вчити слова", "📚 Learn Words", "📚 Kelime Öğren"]))
async def start_quiz(message: Message, state: FSMContext, session: AsyncSession):
    """Запуск викторины"""
    user_id = message.from_user.id
    user = await session.get(User, user_id)

    if not user or not user.level:
        lang = user.interface_language if user else "ru"
        await message.answer(get_text("quiz_no_level", lang))
        return

    lang = user.interface_language or "ru"

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

    try:
        question = await generate_question(
            level=user.level,
            session=session,
            user_id=user_id,
            exclude_ids=[],
            mode=user.translation_mode
        )
    except Exception as e:
        print(f"❌ Ошибка генерации вопроса: {e}")
        await message.answer(get_text("quiz_error_generation", lang))
        return

    if not question:
        await message.answer(get_text("quiz_no_words", lang))
        return

    await state.update_data(
        session_id=quiz_session.id,
        current_question=1,
        total_questions=25,
        correct_answers=0,
        errors=[],
        correct_word_id=question['correct_word'].id,
        used_word_ids=[question['correct_word'].id]
    )

    word = question['correct_word']
    mode = user.translation_mode

    if mode.value in ("ru_to_de", "uk_to_de"):
        translation = word.translation_ru if mode.value == "ru_to_de" else word.translation_uk
        example = word.example_ru if mode.value == "ru_to_de" else word.example_uk
        flag = "🏴" if mode.value == "ru_to_de" else "🇺🇦"

        question_text = (
            f"{get_text('quiz_question_number', lang, current=1, total=25)}\n\n"
            f"{flag} <b>{translation.capitalize()}</b>\n\n"
            f"📝 {example}\n\n"
            f"{get_text('quiz_question_choose_word', lang)}"
        )
    else:
        word_display = word.word_de
        if word.article and word.article != '-':
            word_display = f"{word.article} {word.word_de}"

        question_text = (
            f"{get_text('quiz_question_number', lang, current=1, total=25)}\n\n"
            f"🇩🇪 <b>{word_display}</b>\n\n"
            f"📝 {word.example_de}\n\n"
            f"{get_text('quiz_question_choose_translation', lang)}"
        )

    try:
        await message.delete()
    except:
        pass

    old_anchor_id, new_anchor_id = await ensure_anchor(message, session, user, emoji="📚")

    if old_anchor_id:
        current_msg_id = message.message_id
        await delete_messages_fast(message.bot, message.chat.id, old_anchor_id, current_msg_id)

    await message.answer(question_text, reply_markup=get_answer_keyboard(question['options']))
    await state.set_state(QuizStates.answering)


@router.callback_query(F.data.startswith("answer_"), QuizStates.answering)
async def process_answer(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Обработка ответа пользователя"""
    selected_word_id = int(callback.data.split("_")[1])

    data = await state.get_data()
    correct_word_id = data['correct_word_id']
    session_id = data['session_id']
    correct_answers = data['correct_answers']
    errors = data['errors']

    correct_word = await session.get(Word, correct_word_id)
    is_correct = (selected_word_id == correct_word_id)

    session_item = QuizQuestion(
        session_id=session_id,
        word_id=correct_word_id,
        is_correct=is_correct,
        answered_at=datetime.utcnow()
    )
    session.add(session_item)
    await session.commit()

    try:
        await update_word_progress(
            user_id=callback.from_user.id,
            word_id=correct_word_id,
            is_correct=is_correct,
            session=session
        )
    except Exception as e:
        print(f"⚠️ Ошибка обновления прогресса: {e}")

    word_display = correct_word.word_de
    if correct_word.article and correct_word.article != '-':
        word_display = f"{correct_word.article} {correct_word.word_de}"

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"
    mode = user.translation_mode

    if is_correct:
        correct_answers += 1

        if mode.value in ("ru_to_de", "uk_to_de"):
            translation = correct_word.translation_ru if mode.value == "ru_to_de" else correct_word.translation_uk
            example = correct_word.example_ru if mode.value == "ru_to_de" else correct_word.example_uk
            flag = "🏴" if mode.value == "ru_to_de" else "🇺🇦"

            response_text = (
                f"{get_text('quiz_correct', lang)}\n\n"
                f"{flag} <b>{translation.capitalize()}</b> = 🇩🇪 <b>{word_display}</b>\n\n"
                f"🇩🇪 {correct_word.example_de}\n\n"
                f"{flag} {example}"
            )
        else:
            translation = correct_word.translation_ru if mode.value == "de_to_ru" else correct_word.translation_uk
            example = correct_word.example_ru if mode.value == "de_to_ru" else correct_word.example_uk
            flag = "🏴" if mode.value == "de_to_ru" else "🇺🇦"

            response_text = (
                f"{get_text('quiz_correct', lang)}\n\n"
                f"🇩🇪 <b>{word_display}</b> = {flag} <b>{translation.capitalize()}</b>\n\n"
                f"🇩🇪 {correct_word.example_de}\n\n"
                f"{flag} {example}"
            )
    else:
        errors.append(correct_word_id)

        if mode.value in ("ru_to_de", "uk_to_de"):
            translation = correct_word.translation_ru if mode.value == "ru_to_de" else correct_word.translation_uk
            example = correct_word.example_ru if mode.value == "ru_to_de" else correct_word.example_uk
            flag = "🏴" if mode.value == "ru_to_de" else "🇺🇦"

            response_text = (
                f"{get_text('quiz_wrong', lang)}\n\n"
                f"{get_text('quiz_correct_answer', lang)}\n\n"
                f"{flag} <b>{translation.capitalize()}</b> = 🇩🇪 <b>{word_display}</b>\n\n"
                f"🇩🇪 {correct_word.example_de}\n\n"
                f"{flag} {example}"
            )
        else:
            translation = correct_word.translation_ru if mode.value == "de_to_ru" else correct_word.translation_uk
            example = correct_word.example_ru if mode.value == "de_to_ru" else correct_word.example_uk
            flag = "🏴" if mode.value == "de_to_ru" else "🇺🇦"

            response_text = (
                f"{get_text('quiz_wrong', lang)}\n\n"
                f"{get_text('quiz_correct_answer', lang)}\n\n"
                f"🇩🇪 <b>{word_display}</b> = {flag} <b>{translation.capitalize()}</b>\n\n"
                f"🇩🇪 {correct_word.example_de}\n\n"
                f"{flag} {example}"
            )

    await state.update_data(
        correct_answers=correct_answers,
        errors=errors
    )

    await callback.message.edit_text(response_text, reply_markup=get_next_question_keyboard(lang))
    await callback.answer()


@router.callback_query(F.data == "next_question", QuizStates.answering)
async def show_next_question(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Показ следующего вопроса"""
    await callback.answer()

    data = await state.get_data()
    current_question = data['current_question']
    total_questions = data['total_questions']
    correct_answers = data['correct_answers']
    errors = data.get('errors', [])
    used_word_ids = data.get('used_word_ids', [])
    error_words = data.get('error_words', [])

    current_question += 1
    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    if current_question > total_questions:
        # ============================================================================
        # ВИКТОРИНА ЗАВЕРШЕНА - ОБНОВЛЕНИЕ СТАТИСТИКИ
        # ============================================================================
        session_id = data['session_id']
        user_id = callback.from_user.id

        # 1. Обновляем quizzes_passed
        user.quizzes_passed = (user.quizzes_passed or 0) + 1

        # 2. FIXED: Считаем words_learned из UserWord (уникальные выученные слова)
        learned_count_result = await session.execute(
            select(func.count(UserWord.word_id))
            .where(UserWord.user_id == user_id, UserWord.learned == True)
        )
        user.words_learned = learned_count_result.scalar() or 0

        # 3. FIXED: Считаем success_rate как средний процент по всем викторинам
        completed_sessions_result = await session.execute(
            select(QuizSession).where(
                QuizSession.user_id == user_id,
                QuizSession.completed_at.isnot(None)
            )
        )
        all_completed_sessions = completed_sessions_result.scalars().all()

        # Добавляем текущую сессию к подсчёту
        total_q = sum(s.total_questions for s in all_completed_sessions) + total_questions
        total_c = sum(s.correct_answers for s in all_completed_sessions) + correct_answers
        user.success_rate = int((total_c / total_q * 100)) if total_q > 0 else 0

        await session.commit()

        # 4. Обновляем QuizSession
        quiz_session = await session.get(QuizSession, session_id)
        quiz_session.correct_answers = correct_answers
        quiz_session.completed_at = datetime.utcnow()
        await session.commit()

        # 5. Обновляем стрик
        await update_user_activity(session, callback.from_user.id)

        # 6. Формируем результаты
        result_items = await session.execute(
            select(QuizQuestion, Word)
            .join(Word, QuizQuestion.word_id == Word.id)
            .where(QuizQuestion.session_id == session_id)
            .order_by(QuizQuestion.answered_at)
        )
        items = result_items.all()

        details = []
        for item, word in items:
            wd = word.word_de
            if word.article and word.article != '-':
                wd = f"{word.article} {word.word_de}"
            icon = "✅" if item.is_correct else "❌"

            # Перевод зависит от режима
            if user.translation_mode.value in ("de_to_ru", "ru_to_de"):
                trans = word.translation_ru.capitalize()
            else:
                trans = word.translation_uk.capitalize()

            details.append(f"{icon} {wd} — {trans}")

        percentage = (correct_answers / total_questions) * 100
        result_text = (
            f"{get_text('quiz_completed', lang)}\n\n"
            f"{get_text('quiz_result_correct', lang, correct=correct_answers, total=total_questions)}\n"
            f"{get_text('quiz_result_percentage', lang, percentage=f'{percentage:.1f}')}\n\n"
            f"{get_text('quiz_result_details', lang)}\n" + "\n".join(details)
        )

        if errors:
            result_text += "\n\n" + get_text('quiz_result_errors', lang, count=len(errors))

        try:
            await callback.message.delete()
        except:
            pass

        await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text=result_text,
            reply_markup=get_results_keyboard(has_errors=bool(errors), lang=lang)
        )

        saved_errors = errors.copy()
        await state.clear()
        await state.update_data(saved_errors=saved_errors)
        return

    # СЛЕДУЮЩИЙ ВОПРОС
    mode = user.translation_mode

    if error_words:
        # Повтор ошибок
        current_error_index = data.get('current_error_index', 0) + 1

        if current_error_index >= len(error_words):
            await callback.message.answer(get_text("quiz_error_next", lang))
            await state.clear()
            return

        next_word_id = error_words[current_error_index]
        next_word = await session.get(Word, next_word_id)

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

        if mode.value in ("ru_to_de", "uk_to_de"):
            word_display = next_word.word_de
            if next_word.article and next_word.article != '-':
                word_display = f"{next_word.article} {next_word.word_de}"
            options = [(next_word.id, word_display)]
            for d in distractors[:3]:
                dd = d.word_de
                if d.article and d.article != '-':
                    dd = f"{d.article} {d.word_de}"
                options.append((d.id, dd))
        elif mode.value == "de_to_uk":
            options = [(next_word.id, next_word.translation_uk.capitalize())]
            options.extend([(d.id, d.translation_uk.capitalize()) for d in distractors[:3]])
        else:
            options = [(next_word.id, next_word.translation_ru.capitalize())]
            options.extend([(d.id, d.translation_ru.capitalize()) for d in distractors[:3]])

        random.shuffle(options)

        await state.update_data(
            current_question=current_question,
            correct_word_id=next_word_id,
            current_error_index=current_error_index
        )

        display_total = len(error_words)

        if mode.value in ("ru_to_de", "uk_to_de"):
            translation = next_word.translation_ru if mode.value == "ru_to_de" else next_word.translation_uk
            example = next_word.example_ru if mode.value == "ru_to_de" else next_word.example_uk
            flag = "🏴" if mode.value == "ru_to_de" else "🇺🇦"

            question_text = (
                f"{get_text('quiz_repeat_question', lang, current=current_error_index + 1, total=display_total)}\n\n"
                f"{flag} <b>{translation.capitalize()}</b>\n\n"
                f"📝 {example}\n\n"
                f"{get_text('quiz_question_choose_word', lang)}"
            )
        else:
            word_display = next_word.word_de
            if next_word.article and next_word.article != '-':
                word_display = f"{next_word.article} {next_word.word_de}"

            question_text = (
                f"{get_text('quiz_repeat_question', lang, current=current_error_index + 1, total=display_total)}\n\n"
                f"🇩🇪 <b>{word_display}</b>\n\n"
                f"📝 {next_word.example_de}\n\n"
                f"{get_text('quiz_question_choose_translation', lang)}"
            )

        await callback.message.edit_text(question_text, reply_markup=get_answer_keyboard(options))
        return

    # Обычная викторина
    question = None
    attempts = 0

    while attempts < 10:
        try:
            question = await generate_question(
                level=user.level,
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
        await callback.message.answer(get_text("quiz_error_generate", lang))
        await state.clear()
        return

    used_word_ids.append(question['correct_word'].id)

    await state.update_data(
        current_question=current_question,
        correct_word_id=question['correct_word'].id,
        used_word_ids=used_word_ids
    )

    word = question['correct_word']

    if mode.value in ("ru_to_de", "uk_to_de"):
        translation = word.translation_ru if mode.value == "ru_to_de" else word.translation_uk
        example = word.example_ru if mode.value == "ru_to_de" else word.example_uk
        flag = "🏴" if mode.value == "ru_to_de" else "🇺🇦"

        question_text = (
            f"{get_text('quiz_question_number', lang, current=current_question, total=total_questions)}\n\n"
            f"{flag} <b>{translation.capitalize()}</b>\n\n"
            f"📝 {example}\n\n"
            f"{get_text('quiz_question_choose_word', lang)}"
        )
    else:
        word_display = word.word_de
        if word.article and word.article != '-':
            word_display = f"{word.article} {word.word_de}"

        question_text = (
            f"{get_text('quiz_question_number', lang, current=current_question, total=total_questions)}\n\n"
            f"🇩🇪 <b>{word_display}</b>\n\n"
            f"📝 {word.example_de}\n\n"
            f"{get_text('quiz_question_choose_translation', lang)}"
        )

    await callback.message.edit_text(question_text, reply_markup=get_answer_keyboard(question['options']))


@router.callback_query(F.data == "repeat_errors")
async def repeat_errors(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Повтор ошибок"""
    data = await state.get_data()
    errors = data.get('saved_errors', [])

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    if not errors:
        await callback.message.answer(get_text("quiz_no_errors", lang))
        await callback.answer()
        return

    quiz_session = QuizSession(
        user_id=callback.from_user.id,
        level=user.level,
        translation_mode=user.translation_mode,
        total_questions=len(errors),
        correct_answers=0,
    )

    session.add(quiz_session)
    await session.flush()
    await session.commit()

    first_word_id = errors[0]
    first_word = await session.get(Word, first_word_id)

    distractors = await get_distractors(first_word, session)

    if len(distractors) < 3:
        result = await session.execute(
            select(Word).where(
                Word.level == user.level,
                Word.id != first_word_id,
                Word.id.not_in([d.id for d in distractors])
            )
        )
        all_words = result.scalars().all()
        if all_words:
            needed = min(3 - len(distractors), len(all_words))
            distractors.extend(random.sample(all_words, needed))

    mode = user.translation_mode

    if mode.value in ("ru_to_de", "uk_to_de"):
        word_display = first_word.word_de
        if first_word.article and first_word.article != '-':
            word_display = f"{first_word.article} {first_word.word_de}"
        options = [(first_word.id, word_display)]
        for d in distractors[:3]:
            dd = d.word_de
            if d.article and d.article != '-':
                dd = f"{d.article} {d.word_de}"
            options.append((d.id, dd))
    elif mode.value == "de_to_uk":
        options = [(first_word.id, first_word.translation_uk.capitalize())]
        options.extend([(d.id, d.translation_uk.capitalize()) for d in distractors[:3]])
    else:
        options = [(first_word.id, first_word.translation_ru.capitalize())]
        options.extend([(d.id, d.translation_ru.capitalize()) for d in distractors[:3]])

    random.shuffle(options)

    await state.update_data(
        session_id=quiz_session.id,
        current_question=1,
        total_questions=len(errors),
        correct_answers=0,
        errors=[],
        correct_word_id=first_word_id,
        error_words=errors,
        current_error_index=0
    )

    if mode.value in ("ru_to_de", "uk_to_de"):
        translation = first_word.translation_ru if mode.value == "ru_to_de" else first_word.translation_uk
        example = first_word.example_ru if mode.value == "ru_to_de" else first_word.example_uk
        flag = "🏴" if mode.value == "ru_to_de" else "🇺🇦"

        question_text = (
            f"{get_text('quiz_repeat_title', lang)}\n"
            f"{get_text('quiz_question_number', lang, current=1, total=len(errors))}\n\n"
            f"{flag} <b>{translation.capitalize()}</b>\n\n"
            f"📝 {example}\n\n"
            f"{get_text('quiz_question_choose_word', lang)}"
        )
    else:
        word_display = first_word.word_de
        if first_word.article and first_word.article != '-':
            word_display = f"{first_word.article} {first_word.word_de}"

        question_text = (
            f"{get_text('quiz_repeat_title', lang)}\n"
            f"{get_text('quiz_question_number', lang, current=1, total=len(errors))}\n\n"
            f"🇩🇪 <b>{word_display}</b>\n\n"
            f"📝 {first_word.example_de}\n\n"
            f"{get_text('quiz_question_choose_translation', lang)}"
        )

    try:
        await callback.message.delete()
    except:
        pass

    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text=question_text,
        reply_markup=get_answer_keyboard(options)
    )

    await state.set_state(QuizStates.answering)
    await callback.answer()