"""
Игровая логика викторины с поддержкой локализации и режимов викторины

ИЗМЕНЕНИЯ:
1. ✅ generate_question теперь получает user для фильтрации по quiz_mode
2. ✅ QuizSession сохраняет quiz_mode и quiz_category
3. ✅ 3 кнопки после завершения: Режим викторины, Повторить ошибки, Ошибка перевода
4. ✅ Режим DIFFICULT: проверка наличия сложных слов перед стартом
5. ✅ Репорт ошибок: state data (report_session_id, report_word_ids) после завершения
6. ✅ FIX: report_word_ids сохраняется от основной викторины даже после error_repeat
"""

import random
from datetime import datetime, date, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

import logging

logger = logging.getLogger(__name__)

from app.bot.utils import delete_messages_fast, ensure_anchor
from app.database.models import User, QuizSession, QuizQuestion, Word, UserWord
from app.database.enums import QuizMode
from app.services.monthly_leaderboard_service import update_monthly_stats
from app.bot.states import QuizStates
from app.bot.keyboards import get_answer_keyboard, get_main_menu_keyboard
from app.locales import get_text
from app.services.quiz_service import (
    generate_question,
    update_word_progress,
    get_distractors,
    STRUGGLING_THRESHOLD,
)

router = Router()


# ============================================================================
# ХЕЛПЕРЫ ДЛЯ ЯЗЫКОВ
# ============================================================================

def get_translation_for_mode(word: Word, mode_value: str) -> str:
    mapping = {
        "de_to_ru": word.translation_ru,
        "ru_to_de": word.translation_ru,
        "de_to_uk": word.translation_uk,
        "uk_to_de": word.translation_uk,
        "de_to_en": getattr(word, 'translation_en', None),
        "en_to_de": getattr(word, 'translation_en', None),
        "de_to_tr": getattr(word, 'translation_tr', None),
        "tr_to_de": getattr(word, 'translation_tr', None),
    }
    return mapping.get(mode_value.lower()) or word.translation_ru or ""

def get_example_for_mode(word: Word, mode_value: str) -> str:
    mapping = {
        "de_to_ru": word.example_ru,
        "ru_to_de": word.example_ru,
        "de_to_uk": word.example_uk,
        "uk_to_de": word.example_uk,
        "de_to_en": getattr(word, 'example_en', None),
        "en_to_de": getattr(word, 'example_en', None),
        "de_to_tr": getattr(word, 'example_tr', None),
        "tr_to_de": getattr(word, 'example_tr', None),
    }
    return mapping.get(mode_value.lower()) or word.example_ru or ""


def get_flag_for_mode(mode_value: str) -> str:
    mapping = {
        "de_to_ru": "🏴", "ru_to_de": "🏴",
        "de_to_uk": "🇺🇦", "uk_to_de": "🇺🇦",
        "de_to_en": "🇬🇧", "en_to_de": "🇬🇧",
        "de_to_tr": "🇹🇷", "tr_to_de": "🇹🇷",
    }
    return mapping.get(mode_value.lower(), "🏴")


def is_reverse_mode(mode_value: str) -> bool:
    return mode_value.lower() in ("ru_to_de", "uk_to_de", "en_to_de", "tr_to_de")


def get_word_display(word: Word) -> str:
    if word.article and word.article != '-':
        return f"{word.article} {word.word_de}"
    return word.word_de


# ============================================================================
# УТИЛИТЫ
# ============================================================================

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
    """3 кнопки после завершения викторины"""
    buttons = []

    # 1. Повторить ошибки (если есть) — ПЕРВАЯ
    if has_errors:
        buttons.append([
            InlineKeyboardButton(
                text=get_text("quiz_btn_repeat_errors", lang),
                callback_data="repeat_errors"
            )
        ])

    # 2. Режим викторины (быстрый переход в настройки)
    buttons.append([
        InlineKeyboardButton(
            text=get_text("quiz_btn_change_mode", lang),
            callback_data="settings_quiz_mode"
        )
    ])

    # 3. Ошибка перевода → report.py
    buttons.append([
        InlineKeyboardButton(
            text=get_text("quiz_btn_report_error", lang),
            callback_data="report_translation_error"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ============================================================================
# СТАРТ ВИКТОРИНЫ
# ============================================================================

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

    # Проверка для режима DIFFICULT: есть ли сложные слова
    if user.quiz_mode == QuizMode.DIFFICULT:
        difficult_count = await session.execute(
            select(func.count(UserWord.word_id))
            .where(
                UserWord.user_id == user_id,
                UserWord.learned == False,
                UserWord.times_shown >= 2,
                (UserWord.times_correct * 100.0 / UserWord.times_shown) < STRUGGLING_THRESHOLD
            )
        )
        count = difficult_count.scalar() or 0
        if count == 0:
            await message.answer(get_text("qmode_difficult_empty", lang))
            return
        if count < 4:  # Минимум 4 слова (1 правильный + 3 дистрактора)
            await message.answer(get_text("qmode_difficult_few", lang, count=count))
            return

    # Количество вопросов: для DIFFICULT — сколько есть, для остальных — 25
    if user.quiz_mode == QuizMode.DIFFICULT:
        difficult_count_result = await session.execute(
            select(func.count(UserWord.word_id))
            .where(
                UserWord.user_id == user_id,
                UserWord.learned == False,
                UserWord.times_shown >= 2,
                (UserWord.times_correct * 100.0 / UserWord.times_shown) < STRUGGLING_THRESHOLD
            )
        )
        quiz_total = min(difficult_count_result.scalar() or 25, 25)
    else:
        quiz_total = 25

    quiz_session = QuizSession(
        user_id=user_id,
        level=user.level,
        translation_mode=user.translation_mode,
        total_questions=quiz_total,
        correct_answers=0,
        quiz_mode=user.quiz_mode.value if user.quiz_mode else "level",
        quiz_category=user.quiz_category,
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
            mode=user.translation_mode,
            user=user,
        )
    except Exception as e:
        logger.error(f"Ошибка генерации вопроса: {e}")
        await message.answer(get_text("quiz_error_generation", lang))
        return

    if not question:
        await message.answer(get_text("quiz_no_words", lang))
        return

    await state.update_data(
        session_id=quiz_session.id,
        current_question=1,
        total_questions=quiz_total,
        correct_answers=0,
        errors=[],
        correct_word_id=question['correct_word'].id,
        used_word_ids=[question['correct_word'].id],
        is_error_repeat=False,
    )

    word = question['correct_word']
    mode = user.translation_mode
    mode_val = mode.value.lower()

    if is_reverse_mode(mode_val):
        translation = get_translation_for_mode(word, mode_val)
        example = get_example_for_mode(word, mode_val)
        flag = get_flag_for_mode(mode_val)

        question_text = (
            f"{get_text('quiz_question_number', lang, current=1, total=quiz_total)}\n\n"
            f"{flag} <b>{translation.capitalize()}</b>\n\n"
            f"📝 {example}\n\n"
            f"{get_text('quiz_question_choose_word', lang)}"
        )
    else:
        word_display = get_word_display(word)

        question_text = (
            f"{get_text('quiz_question_number', lang, current=1, total=quiz_total)}\n\n"
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


# ============================================================================
# ОБРАБОТКА ОТВЕТА
# ============================================================================

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
    if not correct_word:
        await callback.answer("❌ Error", show_alert=True)
        await state.clear()
        return

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
        logger.warning(f"Ошибка обновления прогресса: {e}")

    word_display = get_word_display(correct_word)

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"
    mode = user.translation_mode
    mode_val = mode.value.lower()

    translation = get_translation_for_mode(correct_word, mode_val)
    example = get_example_for_mode(correct_word, mode_val)
    flag = get_flag_for_mode(mode_val)

    if is_correct:
        correct_answers += 1

        if is_reverse_mode(mode_val):
            response_text = (
                f"{get_text('quiz_correct', lang)}\n\n"
                f"{flag} <b>{translation.capitalize()}</b> = 🇩🇪 <b>{word_display}</b>\n\n"
                f"🇩🇪 {correct_word.example_de}\n\n"
                f"{flag} {example}"
            )
        else:
            response_text = (
                f"{get_text('quiz_correct', lang)}\n\n"
                f"🇩🇪 <b>{word_display}</b> = {flag} <b>{translation.capitalize()}</b>\n\n"
                f"🇩🇪 {correct_word.example_de}\n\n"
                f"{flag} {example}"
            )
    else:
        errors.append(correct_word_id)

        if is_reverse_mode(mode_val):
            response_text = (
                f"{get_text('quiz_wrong', lang)}\n\n"
                f"{get_text('quiz_correct_answer', lang)}\n\n"
                f"{flag} <b>{translation.capitalize()}</b> = 🇩🇪 <b>{word_display}</b>\n\n"
                f"🇩🇪 {correct_word.example_de}\n\n"
                f"{flag} {example}"
            )
        else:
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


# ============================================================================
# СЛЕДУЮЩИЙ ВОПРОС
# ============================================================================

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

    is_error_repeat = data.get('is_error_repeat', False)
    error_words = data.get('error_words', [])
    current_error_index = data.get('current_error_index', 0)

    current_question += 1
    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"
    mode_val = user.translation_mode.value.lower()

    if current_question > total_questions:
        # ============================================================================
        # ВИКТОРИНА ЗАВЕРШЕНА
        # ============================================================================
        session_id = data['session_id']
        user_id = callback.from_user.id

        quiz_session = await session.get(QuizSession, session_id)
        if quiz_session:
            quiz_session.correct_answers = correct_answers
            quiz_session.completed_at = datetime.utcnow()
            quiz_session.is_completed = True
            await session.commit()

        if not is_error_repeat:
            # === ТОЛЬКО ДЛЯ ОБЫЧНОЙ ВИКТОРИНЫ: обновляем статистику ===
            user.quizzes_passed = (user.quizzes_passed or 0) + 1
            user.last_quiz_date = date.today()

            learned_count_result = await session.execute(
                select(func.count(UserWord.word_id))
                .where(UserWord.user_id == user_id, UserWord.learned == True)
            )
            user.words_learned = learned_count_result.scalar() or 0

            completed_sessions_result = await session.execute(
                select(QuizSession).where(
                    QuizSession.user_id == user_id,
                    QuizSession.completed_at.isnot(None)
                )
            )
            all_completed_sessions = completed_sessions_result.scalars().all()

            total_q = sum(s.total_questions for s in all_completed_sessions)
            total_c = sum(s.correct_answers for s in all_completed_sessions)
            user.success_rate = int((total_c / total_q * 100)) if total_q > 0 else 0

            await session.commit()

            try:
                await update_monthly_stats(
                    user_id=user_id,
                    session=session,
                    quiz_session_id=session_id
                )
            except Exception as e:
                logger.warning(f"Ошибка обновления месячной статистики: {e}")

            await update_user_activity(session, callback.from_user.id)

        # === Результаты ===
        result_items = await session.execute(
            select(QuizQuestion, Word)
            .join(Word, QuizQuestion.word_id == Word.id)
            .where(QuizQuestion.session_id == session_id)
            .order_by(QuizQuestion.answered_at)
        )
        items = result_items.all()

        details = []
        for item, word in items:
            wd = get_word_display(word)
            icon = "✅" if item.is_correct else "❌"
            trans = get_translation_for_mode(word, mode_val)
            details.append(f"{icon} {wd} — {trans.capitalize()}")

        percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0

        if is_error_repeat:
            result_text = (
                f"🔄 {get_text('quiz_completed', lang)}\n\n"
                f"{get_text('quiz_result_correct', lang, correct=correct_answers, total=total_questions)}\n"
                f"{get_text('quiz_result_percentage', lang, percentage=f'{percentage:.1f}')}\n\n"
                f"{get_text('quiz_result_details', lang)}\n" + "\n".join(details)
            )
        else:
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

        # Кнопки: всегда полный набор (повтор если есть ошибки)
        keyboard = get_results_keyboard(has_errors=bool(errors), lang=lang)

        await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text=result_text,
            reply_markup=keyboard
        )

        # === STATE DATA для повтора ошибок и репорта ===
        # FIX: после error_repeat сохраняем report_word_ids от ОСНОВНОЙ викторины
        saved_errors = errors.copy()

        # Сохраняем старые report данные перед clear (нужны после error_repeat)
        old_report_word_ids = data.get('report_word_ids', [])
        old_report_session_id = data.get('report_session_id')

        await state.clear()

        if is_error_repeat:
            # После повтора ошибок — восстанавливаем report данные от основной викторины
            await state.update_data(
                saved_errors=saved_errors,
                report_session_id=old_report_session_id,
                report_word_ids=old_report_word_ids,
            )
        else:
            # После основной викторины — сохраняем все слова для репорта
            report_word_ids = [w.id for _, w in items]
            await state.update_data(
                saved_errors=saved_errors,
                report_session_id=session_id,
                report_word_ids=report_word_ids,
            )
        return

    # ============================================================================
    # СЛЕДУЮЩИЙ ВОПРОС
    # ============================================================================

    if is_error_repeat:
        current_error_index += 1

        if current_error_index >= len(error_words):
            logger.warning("error_repeat: current_error_index вышел за пределы error_words")
            await state.clear()
            return

        next_word_id = error_words[current_error_index]
        word = await session.get(Word, next_word_id)

        if not word:
            await callback.message.answer(get_text("quiz_error_generate", lang))
            await state.clear()
            return

        distractors = await get_distractors(word, session, user=user)
        if len(distractors) < 3:
            from app.services.quiz_service import get_additional_distractors
            additional = await get_additional_distractors(
                word, distractors, user.level, session, 3 - len(distractors), user=user
            )
            distractors.extend(additional)

        if is_reverse_mode(mode_val):
            options = [(word.id, get_word_display(word))]
            for d in distractors[:3]:
                options.append((d.id, get_word_display(d)))
        else:
            trans = get_translation_for_mode(word, mode_val)
            options = [(word.id, (trans or "").capitalize())]
            for d in distractors[:3]:
                d_trans = get_translation_for_mode(d, mode_val)
                options.append((d.id, (d_trans or "").capitalize()))

        random.shuffle(options)

        await state.update_data(
            current_question=current_question,
            correct_word_id=word.id,
            current_error_index=current_error_index
        )
    else:
        question = None
        attempts = 0

        while attempts < 10:
            try:
                question = await generate_question(
                    level=user.level,
                    session=session,
                    user_id=callback.from_user.id,
                    exclude_ids=used_word_ids,
                    mode=user.translation_mode,
                    user=user,
                )
            except Exception as e:
                logger.error(f"Ошибка генерации вопроса: {e}")
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
        options = question['options']

    # === ОТОБРАЖЕНИЕ ВОПРОСА ===
    if is_reverse_mode(mode_val):
        translation = get_translation_for_mode(word, mode_val)
        example = get_example_for_mode(word, mode_val)
        flag = get_flag_for_mode(mode_val)

        prefix = f"{get_text('quiz_repeat_title', lang)}\n" if is_error_repeat else ""
        question_text = (
            f"{prefix}"
            f"{get_text('quiz_question_number', lang, current=current_question, total=total_questions)}\n\n"
            f"{flag} <b>{translation.capitalize()}</b>\n\n"
            f"📝 {example}\n\n"
            f"{get_text('quiz_question_choose_word', lang)}"
        )
    else:
        word_display = get_word_display(word)

        prefix = f"{get_text('quiz_repeat_title', lang)}\n" if is_error_repeat else ""
        question_text = (
            f"{prefix}"
            f"{get_text('quiz_question_number', lang, current=current_question, total=total_questions)}\n\n"
            f"🇩🇪 <b>{word_display}</b>\n\n"
            f"📝 {word.example_de}\n\n"
            f"{get_text('quiz_question_choose_translation', lang)}"
        )

    await callback.message.edit_text(question_text, reply_markup=get_answer_keyboard(options))


# ============================================================================
# ПОВТОР ОШИБОК
# ============================================================================

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
        quiz_mode="error_repeat",
        quiz_category=None,
    )

    session.add(quiz_session)
    await session.flush()
    await session.commit()

    first_word_id = errors[0]
    first_word = await session.get(Word, first_word_id)

    if not first_word:
        await callback.message.answer(get_text("quiz_error_next", lang))
        await callback.answer()
        return

    distractors = await get_distractors(first_word, session, user=user)

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
    mode_val = mode.value.lower()

    if is_reverse_mode(mode_val):
        word_display = get_word_display(first_word)
        options = [(first_word.id, word_display)]
        for d in distractors[:3]:
            dd = get_word_display(d)
            options.append((d.id, dd))
    else:
        trans = get_translation_for_mode(first_word, mode_val)
        options = [(first_word.id, trans.capitalize())]
        for d in distractors[:3]:
            d_trans = get_translation_for_mode(d, mode_val)
            options.append((d.id, d_trans.capitalize()))

    random.shuffle(options)

    # Сохраняем report данные от основной викторины перед обновлением state
    old_report_word_ids = data.get('report_word_ids', [])
    old_report_session_id = data.get('report_session_id')

    await state.update_data(
        session_id=quiz_session.id,
        current_question=1,
        total_questions=len(errors),
        correct_answers=0,
        errors=[],
        correct_word_id=first_word_id,
        error_words=errors,
        current_error_index=0,
        is_error_repeat=True,
        # Сохраняем report данные от основной викторины
        report_word_ids=old_report_word_ids,
        report_session_id=old_report_session_id,
    )

    if is_reverse_mode(mode_val):
        translation = get_translation_for_mode(first_word, mode_val)
        example = get_example_for_mode(first_word, mode_val)
        flag = get_flag_for_mode(mode_val)

        question_text = (
            f"{get_text('quiz_repeat_title', lang)}\n"
            f"{get_text('quiz_question_number', lang, current=1, total=len(errors))}\n\n"
            f"{flag} <b>{translation.capitalize()}</b>\n\n"
            f"📝 {example}\n\n"
            f"{get_text('quiz_question_choose_word', lang)}"
        )
    else:
        word_display = get_word_display(first_word)

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