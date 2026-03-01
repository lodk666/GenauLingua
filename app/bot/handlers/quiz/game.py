"""
Игровая логика викторины с поддержкой локализации
"""

import random
import asyncio
from datetime import datetime, date, timedelta

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.models import User, QuizSession, QuizQuestion, Word
from app.bot.states import QuizStates
from app.bot.keyboards import get_answer_keyboard, get_main_menu_keyboard
from app.locales import get_text
from app.services.quiz_service import (
    generate_question,
    update_word_progress,
    get_distractors,
)

router = Router()

X_TO_DE = {"ru_to_de", "uk_to_de", "en_to_de", "tr_to_de"}
DE_TO_X = {"de_to_ru", "de_to_uk", "de_to_en", "de_to_tr"}

MODE_LANG_MAP = {
    "ru_to_de": ("ru", "🏴"),
    "uk_to_de": ("uk", "🇺🇦"),
    "en_to_de": ("en", "🇬🇧"),
    "tr_to_de": ("tr", "🇹🇷"),
    "de_to_ru": ("ru", "🏴"),
    "de_to_uk": ("uk", "🇺🇦"),
    "de_to_en": ("en", "🇬🇧"),
    "de_to_tr": ("tr", "🇹🇷"),
}


def _mode_val(user: User) -> str:
    return (getattr(user.translation_mode, "value", None) or "").lower()


def _lang_pack_by_mode(mode_val: str):
    return MODE_LANG_MAP.get(mode_val)


def _get_translation(word: Word, lang_code: str) -> str:
    val = getattr(word, f"translation_{lang_code}", None)
    if not val and hasattr(word, "get_translation"):
        val = word.get_translation(lang_code)
    return (val or "").strip()


def _get_example(word: Word, lang_code: str) -> str:
    val = getattr(word, f"example_{lang_code}", None)
    if not val and hasattr(word, "get_example"):
        val = word.get_example(lang_code)
    return (val or "").strip()


def _word_display(word: Word) -> str:
    wd = word.word_de
    if word.article and word.article != "-":
        wd = f"{word.article} {word.word_de}"
    return wd


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


@router.message(F.text.in_(["📚 Учить слова", "📚 Вчити слова", "📚 Learn words", "📚 Kelime öğren"]))
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
        start_source='menu',  # Запущено из главного меню
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
        correct_word_id=question["correct_word"].id,
        used_word_ids=[question["correct_word"].id],
        question_shown_at=datetime.utcnow()  # Сохраняем время показа вопроса
    )

    word = question["correct_word"]
    mode_val = _mode_val(user)

    if mode_val in X_TO_DE:
        lang_code, flag = _lang_pack_by_mode(mode_val)
        translation = _get_translation(word, lang_code)
        example = _get_example(word, lang_code)

        question_text = (
            f"{get_text('quiz_question_number', lang, current=1, total=25)}\n\n"
            f"{flag} <b>{translation.capitalize()}</b>\n\n"
            f"📝 {example}\n\n"
            f"{get_text('quiz_question_choose_word', lang)}"
        )
    else:
        word_display = _word_display(word)
        question_text = (
            f"{get_text('quiz_question_number', lang, current=1, total=25)}\n\n"
            f"🇩🇪 <b>{word_display}</b>\n\n"
            f"📝 {word.example_de or ''}\n\n"
            f"{get_text('quiz_question_choose_translation', lang)}"
        )

    try:
        await message.delete()
    except Exception:
        pass

    old_anchor_id, _new_anchor_id = await ensure_anchor(message, session, user, emoji="📚")

    if old_anchor_id:
        current_msg_id = message.message_id
        await delete_messages_fast(message.bot, message.chat.id, old_anchor_id, current_msg_id)

    await message.answer(question_text, reply_markup=get_answer_keyboard(question["options"]))
    await state.set_state(QuizStates.answering)


@router.callback_query(F.data.startswith("answer_"), QuizStates.answering)
async def process_answer(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Обработка ответа пользователя"""
    selected_word_id = int(callback.data.split("_")[1])

    data = await state.get_data()
    correct_word_id = data["correct_word_id"]
    session_id = data["session_id"]
    correct_answers = data["correct_answers"]
    errors = data["errors"]

    correct_word = await session.get(Word, correct_word_id)
    is_correct = (selected_word_id == correct_word_id)

    # Считаем время ответа (если есть timestamp в state)
    question_shown_at = data.get("question_shown_at")
    response_time_seconds = None
    if question_shown_at:
        response_time = (datetime.utcnow() - question_shown_at).total_seconds()
        response_time_seconds = int(response_time)

    # Логируем вопрос в историю сессии
    session_item = QuizQuestion(
        session_id=session_id,
        word_id=correct_word_id,
        is_correct=is_correct,
        answered_at=datetime.utcnow(),
        response_time_seconds=response_time_seconds
    )
    session.add(session_item)
    await session.commit()

    # Обновляем прогресс
    try:
        await update_word_progress(
            user_id=callback.from_user.id,
            word_id=correct_word_id,
            is_correct=is_correct,
            session=session
        )
    except Exception as e:
        print(f"⚠️ Ошибка обновления прогресса: {e}")

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"
    mode_val = _mode_val(user)

    word_display = _word_display(correct_word)

    pack = _lang_pack_by_mode(mode_val)
    lang_code, flag = pack if pack else ("ru", "🏴")

    translation = _get_translation(correct_word, lang_code)
    example_x = _get_example(correct_word, lang_code)
    example_de = correct_word.example_de or ""

    if is_correct:
        correct_answers += 1

        if mode_val in X_TO_DE:
            # X→DE
            response_text = (
                f"{get_text('quiz_correct', lang)}\n\n"
                f"{flag} <b>{translation.capitalize()}</b> = 🇩🇪 <b>{word_display}</b>\n\n"
                f"🇩🇪 {example_de}\n\n"
                f"{flag} {example_x}"
            )
        else:
            # DE→X
            response_text = (
                f"{get_text('quiz_correct', lang)}\n\n"
                f"🇩🇪 <b>{word_display}</b> = {flag} <b>{translation.capitalize()}</b>\n\n"
                f"🇩🇪 {example_de}\n\n"
                f"{flag} {example_x}"
            )
    else:
        errors.append(correct_word_id)

        if mode_val in X_TO_DE:
            response_text = (
                f"{get_text('quiz_wrong', lang)}\n\n"
                f"{get_text('quiz_correct_answer', lang)}\n\n"
                f"{flag} <b>{translation.capitalize()}</b> = 🇩🇪 <b>{word_display}</b>\n\n"
                f"🇩🇪 {example_de}\n\n"
                f"{flag} {example_x}"
            )
        else:
            response_text = (
                f"{get_text('quiz_wrong', lang)}\n\n"
                f"{get_text('quiz_correct_answer', lang)}\n\n"
                f"🇩🇪 <b>{word_display}</b> = {flag} <b>{translation.capitalize()}</b>\n\n"
                f"🇩🇪 {example_de}\n\n"
                f"{flag} {example_x}"
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
    current_question = data["current_question"]
    total_questions = data["total_questions"]
    correct_answers = data["correct_answers"]
    errors = data.get("errors", [])
    used_word_ids = data.get("used_word_ids", [])
    error_words = data.get("error_words", [])

    current_question += 1
    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"
    mode_val = _mode_val(user)

    if current_question > total_questions:
        # ВИКТОРИНА ЗАВЕРШЕНА
        session_id = data["session_id"]

        user.quizzes_passed = (user.quizzes_passed or 0) + 1
        success_rate = int((correct_answers / total_questions) * 100)
        user.success_rate = success_rate
        unique_used = set(used_word_ids) if used_word_ids else set()
        user.words_learned = (user.words_learned or 0) + len(unique_used)
        await session.commit()

        quiz_session = await session.get(QuizSession, session_id)
        quiz_session.correct_answers = correct_answers
        quiz_session.completed_at = datetime.utcnow()
        quiz_session.is_completed = True
        quiz_session.exit_reason = 'completed'  # Успешно завершил
        quiz_session.exit_at_question = total_questions  # Дошёл до конца

        # Обновляем last_quiz_date у пользователя
        user.last_quiz_date = date.today()

        await session.commit()

        # Обновляем стрик
        await update_user_activity(session, callback.from_user.id)

        result_items = await session.execute(
            select(QuizQuestion, Word)
            .join(Word, QuizQuestion.word_id == Word.id)
            .where(QuizQuestion.session_id == session_id)
            .order_by(QuizQuestion.answered_at)
        )
        items = result_items.all()

        # Детализация — на том языке, который соответствует режиму
        pack = _lang_pack_by_mode(mode_val)
        lang_code, _flag = pack if pack else ("ru", "🏴")

        details = []
        for item, word in items:
            wd = _word_display(word)
            icon = "✅" if item.is_correct else "❌"
            trans = _get_translation(word, lang_code).capitalize()
            details.append(f"{icon} {wd} — {trans}")

        percentage = (correct_answers / total_questions) * 100
        result_text = (
            f"{get_text('quiz_completed', lang)}\n\n"
            f"{get_text('quiz_result_correct', lang, correct=correct_answers, total=total_questions)}\n"
            f"{get_text('quiz_result_percentage', lang, percentage=f'{percentage:.1f}')}\n\n"
            f"{get_text('quiz_result_details', lang)}\n" + "\n".join(details)
        )

        if errors:
            result_text += "\n\n" + get_text("quiz_result_errors", lang, count=len(errors))

        try:
            await callback.message.delete()
        except Exception:
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
    if error_words:
        # Повтор ошибок
        current_error_index = data.get("current_error_index", 0) + 1

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

        # Варианты ответов при повторе ошибок
        if mode_val in X_TO_DE:
            # варианты = немецкие слова
            options = [(next_word.id, _word_display(next_word))]
            for d in distractors[:3]:
                options.append((d.id, _word_display(d)))
        else:
            # варианты = перевод на язык режима
            pack = _lang_pack_by_mode(mode_val)
            lang_code, _flag = pack if pack else ("ru", "🏴")
            options = [(next_word.id, _get_translation(next_word, lang_code).capitalize())]
            for d in distractors[:3]:
                options.append((d.id, _get_translation(d, lang_code).capitalize()))

        random.shuffle(options)

        await state.update_data(
            current_question=current_question,
            correct_word_id=next_word_id,
            current_error_index=current_error_index,
            question_shown_at=datetime.utcnow()  # Время показа вопроса
        )

        display_total = len(error_words)

        if mode_val in X_TO_DE:
            lang_code, flag = _lang_pack_by_mode(mode_val)
            translation = _get_translation(next_word, lang_code)
            example = _get_example(next_word, lang_code)

            question_text = (
                f"{get_text('quiz_repeat_question', lang, current=current_error_index + 1, total=display_total)}\n\n"
                f"{flag} <b>{translation.capitalize()}</b>\n\n"
                f"📝 {example}\n\n"
                f"{get_text('quiz_question_choose_word', lang)}"
            )
        else:
            word_display = _word_display(next_word)
            question_text = (
                f"{get_text('quiz_repeat_question', lang, current=current_error_index + 1, total=display_total)}\n\n"
                f"🇩🇪 <b>{word_display}</b>\n\n"
                f"📝 {next_word.example_de or ''}\n\n"
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

    used_word_ids.append(question["correct_word"].id)

    await state.update_data(
        current_question=current_question,
        correct_word_id=question["correct_word"].id,
        used_word_ids=used_word_ids,
        question_shown_at=datetime.utcnow()  # Время показа вопроса
    )

    word = question["correct_word"]

    if mode_val in X_TO_DE:
        lang_code, flag = _lang_pack_by_mode(mode_val)
        translation = _get_translation(word, lang_code)
        example = _get_example(word, lang_code)

        question_text = (
            f"{get_text('quiz_question_number', lang, current=current_question, total=total_questions)}\n\n"
            f"{flag} <b>{translation.capitalize()}</b>\n\n"
            f"📝 {example}\n\n"
            f"{get_text('quiz_question_choose_word', lang)}"
        )
    else:
        word_display = _word_display(word)
        question_text = (
            f"{get_text('quiz_question_number', lang, current=current_question, total=total_questions)}\n\n"
            f"🇩🇪 <b>{word_display}</b>\n\n"
            f"📝 {word.example_de or ''}\n\n"
            f"{get_text('quiz_question_choose_translation', lang)}"
        )

    await callback.message.edit_text(question_text, reply_markup=get_answer_keyboard(question["options"]))


@router.callback_query(F.data == "repeat_errors")
async def repeat_errors(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Повтор ошибок"""
    data = await state.get_data()
    errors = data.get("saved_errors", [])

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"
    mode_val = _mode_val(user)

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
        start_source='repeat_errors',  # Запущено из повтора ошибок
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

    # варианты ответов
    if mode_val in X_TO_DE:
        options = [(first_word.id, _word_display(first_word))]
        for d in distractors[:3]:
            options.append((d.id, _word_display(d)))
    else:
        pack = _lang_pack_by_mode(mode_val)
        lang_code, _flag = pack if pack else ("ru", "🏴")
        options = [(first_word.id, _get_translation(first_word, lang_code).capitalize())]
        for d in distractors[:3]:
            options.append((d.id, _get_translation(d, lang_code).capitalize()))

    random.shuffle(options)

    await state.update_data(
        session_id=quiz_session.id,
        current_question=1,
        total_questions=len(errors),
        correct_answers=0,
        errors=[],
        correct_word_id=first_word_id,
        error_words=errors,
        current_error_index=0,
        question_shown_at=datetime.utcnow()  # Время показа вопроса
    )

    # текст вопроса
    if mode_val in X_TO_DE:
        lang_code, flag = _lang_pack_by_mode(mode_val)
        translation = _get_translation(first_word, lang_code)
        example = _get_example(first_word, lang_code)

        question_text = (
            f"{get_text('quiz_repeat_title', lang)}\n"
            f"{get_text('quiz_question_number', lang, current=1, total=len(errors))}\n\n"
            f"{flag} <b>{translation.capitalize()}</b>\n\n"
            f"📝 {example}\n\n"
            f"{get_text('quiz_question_choose_word', lang)}"
        )
    else:
        word_display = _word_display(first_word)
        question_text = (
            f"{get_text('quiz_repeat_title', lang)}\n"
            f"{get_text('quiz_question_number', lang, current=1, total=len(errors))}\n\n"
            f"🇩🇪 <b>{word_display}</b>\n\n"
            f"📝 {first_word.example_de or ''}\n\n"
            f"{get_text('quiz_question_choose_translation', lang)}"
        )

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text=question_text,
        reply_markup=get_answer_keyboard(options)
    )

    await state.set_state(QuizStates.answering)
    await callback.answer()