"""
Репорт ошибок перевода

Flow:
1. Нажал «📝 Помилка перекладу» → список слов викторины (только кнопки, текст не трогаем)
2. Выбрал слова (✅ галочки) → кнопка «Підтвердити (N)»
3. Підтвердити → «Відправити» + «Назад»
4. Відправити → сохраняет в БД, alert, возврат кнопок результата

Защита:
- UNIQUE(user_id, word_id) — одно слово репортится один раз
- Лимит 20 репортов в сутки
- Уже зарепорченные слова показываются с ✔️ (некликабельные)
"""

import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database.models import User, Word, TranslationReport
from app.locales import get_text

logger = logging.getLogger(__name__)

router = Router()

WORDS_PER_PAGE = 10
DAILY_REPORT_LIMIT = 20


# ============================================================================
# ХЕЛПЕРЫ
# ============================================================================

def _get_word_label(word: Word, mode_val: str) -> str:
    """Сформировать label для слова: der Tisch — Стіл"""
    if word.article and word.article != '-':
        de_part = f"{word.article} {word.word_de}"
    else:
        de_part = word.word_de

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
    trans = mapping.get(mode_val.lower()) or word.translation_ru or ""

    return f"{de_part} — {trans.capitalize()}"


async def _get_already_reported_ids(user_id: int, session: AsyncSession) -> set[int]:
    """Получить word_id которые юзер уже репортил"""
    result = await session.execute(
        select(TranslationReport.word_id)
        .where(TranslationReport.user_id == user_id)
    )
    return {row[0] for row in result.all()}


async def _get_today_report_count(user_id: int, session: AsyncSession) -> int:
    """Количество репортов юзера за сегодня"""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    result = await session.execute(
        select(func.count())
        .select_from(TranslationReport)
        .where(
            TranslationReport.user_id == user_id,
            TranslationReport.created_at >= today_start
        )
    )
    return result.scalar() or 0


def _build_word_list_keyboard(
    word_labels: dict,
    selected: list[int],
    already_reported: set[int],
    page: int,
    lang: str,
) -> InlineKeyboardMarkup:
    """Клавиатура со списком слов + пагинация + кнопки"""
    word_ids = list(word_labels.keys())
    total_pages = max(1, (len(word_ids) + WORDS_PER_PAGE - 1) // WORDS_PER_PAGE)
    page = min(page, total_pages - 1)

    start = page * WORDS_PER_PAGE
    end = start + WORDS_PER_PAGE
    page_words = word_ids[start:end]

    buttons = []
    for wid in page_words:
        label = word_labels[wid]

        if wid in already_reported:
            # Уже отправлено — показываем ✔️, клик → alert
            display = f"✔️ {label}"
            if len(display) > 50:
                display = display[:47] + "…"
            buttons.append([InlineKeyboardButton(
                text=display,
                callback_data=f"report_already_{wid}"
            )])
        else:
            # Можно выбрать
            check = "✅ " if wid in selected else ""
            display = f"{check}{label}"
            if len(display) > 50:
                display = display[:47] + "…"
            buttons.append([InlineKeyboardButton(
                text=display,
                callback_data=f"report_toggle_{wid}"
            )])

    # Пагинация
    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton(text="◀", callback_data=f"report_page_{page - 1}"))
        nav_row.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton(text="▶", callback_data=f"report_page_{page + 1}"))
        buttons.append(nav_row)

    # Кнопка подтверждения (если выбрано ≥1)
    if selected:
        buttons.append([InlineKeyboardButton(
            text=get_text("report_btn_confirm", lang, count=len(selected)),
            callback_data="report_confirm"
        )])

    # Назад
    buttons.append([InlineKeyboardButton(
        text=get_text("btn_back", lang),
        callback_data="report_cancel"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _build_confirm_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения: Відправити + Назад"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=get_text("report_btn_send", lang),
            callback_data="report_send"
        )],
        [InlineKeyboardButton(
            text=get_text("btn_back", lang),
            callback_data="report_back_to_select"
        )]
    ])


def _get_results_keyboard_lazy(has_errors: bool, lang: str) -> InlineKeyboardMarkup:
    """Восстановить исходные кнопки результата"""
    buttons = []

    if has_errors:
        buttons.append([InlineKeyboardButton(
            text=get_text("quiz_btn_repeat_errors", lang),
            callback_data="repeat_errors"
        )])

    buttons.append([InlineKeyboardButton(
        text=get_text("quiz_btn_change_mode", lang),
        callback_data="settings_quiz_mode"
    )])

    buttons.append([InlineKeyboardButton(
        text=get_text("quiz_btn_report_error", lang),
        callback_data="report_translation_error"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ============================================================================
# НАЧАЛО РЕПОРТА — показать список слов
# ============================================================================

@router.callback_query(F.data == "report_translation_error")
async def report_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Начать репорт: показать список слов из викторины"""
    data = await state.get_data()
    report_word_ids = data.get("report_word_ids", [])

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"
    mode_val = user.translation_mode.value.lower() if user.translation_mode else "de_to_ru"

    if not report_word_ids:
        await callback.answer(get_text("report_no_words", lang), show_alert=True)
        return

    # Проверяем дневной лимит
    today_count = await _get_today_report_count(callback.from_user.id, session)
    if today_count >= DAILY_REPORT_LIMIT:
        await callback.answer(get_text("report_daily_limit", lang), show_alert=True)
        return

    # Получаем уже зарепорченные
    already_reported = await _get_already_reported_ids(callback.from_user.id, session)

    # Проверяем есть ли хоть одно новое слово для репорта
    new_available = [wid for wid in report_word_ids if wid not in already_reported]
    if not new_available:
        await callback.answer(get_text("report_all_reported", lang), show_alert=True)
        return

    # Загружаем слова
    result = await session.execute(
        select(Word).where(Word.id.in_(report_word_ids))
    )
    words = result.scalars().all()
    words_by_id = {w.id: w for w in words}

    # Формируем labels в порядке викторины
    word_labels = {}
    for wid in report_word_ids:
        if wid in words_by_id:
            word_labels[wid] = _get_word_label(words_by_id[wid], mode_val)

    if not word_labels:
        await callback.answer(get_text("report_no_words", lang), show_alert=True)
        return

    # Сохраняем в state
    await state.update_data(
        report_word_labels=word_labels,
        report_selected=[],
        report_page=0,
        report_already_reported=list(already_reported),
    )

    keyboard = _build_word_list_keyboard(word_labels, [], already_reported, 0, lang)

    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except Exception:
        pass

    await callback.answer()


# ============================================================================
# КЛИК ПО УЖЕ ЗАРЕПОРЧЕННОМУ СЛОВУ
# ============================================================================

@router.callback_query(F.data.startswith("report_already_"))
async def report_already_reported(callback: CallbackQuery, session: AsyncSession):
    """Клик по слову которое уже зарепорчено — показать alert"""
    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"
    await callback.answer(get_text("report_already_sent", lang), show_alert=False)


# ============================================================================
# ПЕРЕКЛЮЧЕНИЕ ГАЛОЧКИ
# ============================================================================

@router.callback_query(F.data.startswith("report_toggle_"))
async def report_toggle_word(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Переключить галочку у слова"""
    word_id = int(callback.data.replace("report_toggle_", ""))

    data = await state.get_data()
    word_labels = data.get("report_word_labels", {})
    selected = data.get("report_selected", [])
    already_reported = set(data.get("report_already_reported", []))
    page = data.get("report_page", 0)

    word_labels = {int(k): v for k, v in word_labels.items()}

    if word_id in selected:
        selected.remove(word_id)
    else:
        selected.append(word_id)

    await state.update_data(report_selected=selected)

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    keyboard = _build_word_list_keyboard(word_labels, selected, already_reported, page, lang)

    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except Exception:
        pass

    await callback.answer()


# ============================================================================
# ПАГИНАЦИЯ
# ============================================================================

@router.callback_query(F.data.startswith("report_page_"))
async def report_change_page(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Переключить страницу списка слов"""
    page = int(callback.data.replace("report_page_", ""))

    data = await state.get_data()
    word_labels = data.get("report_word_labels", {})
    selected = data.get("report_selected", [])
    already_reported = set(data.get("report_already_reported", []))

    word_labels = {int(k): v for k, v in word_labels.items()}

    await state.update_data(report_page=page)

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    keyboard = _build_word_list_keyboard(word_labels, selected, already_reported, page, lang)

    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except Exception:
        pass

    await callback.answer()


# ============================================================================
# ПОДТВЕРЖДЕНИЕ
# ============================================================================

@router.callback_query(F.data == "report_confirm")
async def report_confirm(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Показать экран подтверждения"""
    data = await state.get_data()
    selected = data.get("report_selected", [])

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    if not selected:
        await callback.answer(get_text("report_none_selected", lang), show_alert=True)
        return

    keyboard = _build_confirm_keyboard(lang)

    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except Exception:
        pass

    await callback.answer()


# ============================================================================
# НАЗАД К СПИСКУ СЛОВ (из экрана подтверждения)
# ============================================================================

@router.callback_query(F.data == "report_back_to_select")
async def report_back_to_select(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Вернуться к списку слов с сохранёнными галочками"""
    data = await state.get_data()
    word_labels = data.get("report_word_labels", {})
    selected = data.get("report_selected", [])
    already_reported = set(data.get("report_already_reported", []))
    page = data.get("report_page", 0)

    word_labels = {int(k): v for k, v in word_labels.items()}

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    keyboard = _build_word_list_keyboard(word_labels, selected, already_reported, page, lang)

    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except Exception:
        pass

    await callback.answer()


# ============================================================================
# ОТПРАВКА РЕПОРТА
# ============================================================================

@router.callback_query(F.data == "report_send")
async def report_send(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Сохранить репорты в БД и вернуть исходные кнопки"""
    data = await state.get_data()
    selected = data.get("report_selected", [])
    report_session_id = data.get("report_session_id")
    saved_errors = data.get("saved_errors", [])

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    if not selected:
        await callback.answer(get_text("report_none_selected", lang), show_alert=True)
        return

    # Проверяем дневной лимит
    today_count = await _get_today_report_count(callback.from_user.id, session)
    remaining = DAILY_REPORT_LIMIT - today_count
    if remaining <= 0:
        await callback.answer(get_text("report_daily_limit", lang), show_alert=True)
        return

    # Ограничиваем количество если лимит близко
    words_to_report = selected[:remaining]

    # Создаём записи (пропускаем дубликаты)
    saved_count = 0
    for word_id in words_to_report:
        existing = await session.execute(
            select(TranslationReport)
            .where(
                TranslationReport.user_id == callback.from_user.id,
                TranslationReport.word_id == word_id
            )
        )
        if existing.scalar_one_or_none():
            continue

        report = TranslationReport(
            user_id=callback.from_user.id,
            word_id=word_id,
            quiz_session_id=report_session_id,
            status="pending",
        )
        session.add(report)
        saved_count += 1

    await session.commit()

    logger.info(
        f"User {callback.from_user.id} reported {saved_count} words "
        f"(selected={len(selected)}, session={report_session_id})"
    )

    # Показываем alert
    if saved_count > 0:
        await callback.answer(
            get_text("report_sent", lang, count=saved_count),
            show_alert=True
        )
    else:
        await callback.answer(
            get_text("report_all_reported", lang),
            show_alert=True
        )

    # Возвращаем исходные кнопки результата
    has_errors = bool(saved_errors)
    keyboard = _get_results_keyboard_lazy(has_errors, lang)

    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except Exception:
        pass


# ============================================================================
# ОТМЕНА — возврат к кнопкам результата
# ============================================================================

@router.callback_query(F.data == "report_cancel")
async def report_cancel(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Отмена репорта — вернуть исходные кнопки результата"""
    data = await state.get_data()
    saved_errors = data.get("saved_errors", [])

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    has_errors = bool(saved_errors)
    keyboard = _get_results_keyboard_lazy(has_errors, lang)

    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except Exception:
        pass

    await callback.answer()