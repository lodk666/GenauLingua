"""
Настройки викторины с поддержкой локализации
Режим викторины, уровень, режим перевода, язык интерфейса
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

import logging

logger = logging.getLogger(__name__)

from app.database.models import User
from app.database.enums import CEFRLevel, TranslationMode, QuizMode, WordCategory
from app.bot.utils import delete_messages_fast, ensure_anchor
from app.bot.keyboards import get_main_menu_keyboard
from app.locales import get_text

router = Router()

# ============================================================================
# КАТЕГОРИИ: списки для пагинации (20 категорий, 10 на страницу)
# ============================================================================

CATEGORIES_PAGE_1 = [
    WordCategory.ARBEIT_BERUF,
    WordCategory.BILDUNG_LERNEN,
    WordCategory.EINKAUFEN_GELD,
    WordCategory.EMOTIONEN_CHARAKTER,
    WordCategory.ESSEN_TRINKEN,
    WordCategory.FREIZEIT_SPORT,
    WordCategory.GESUNDHEIT_MEDIZIN,
    WordCategory.GRAMMATIK,
    WordCategory.KLEIDUNG_MODE,
    WordCategory.KOMMUNIKATION,
]

CATEGORIES_PAGE_2 = [
    WordCategory.KULTUR_KUNST,
    WordCategory.MENSCH_FAMILIE,
    WordCategory.NATUR_WETTER,
    WordCategory.RECHT_STAAT,
    WordCategory.REISEN_TRANSPORT,
    WordCategory.TECHNIK_DIGITAL,
    WordCategory.WIRTSCHAFT,
    WordCategory.WISSENSCHAFT,
    WordCategory.WOHNEN_HAUS,
    WordCategory.ZEIT_ALLTAG,
]


def get_category_display(cat_value: str, lang: str) -> str:
    """Получить локализованное название категории через систему локализации"""
    # Arbeit & Beruf -> cat_arbeit_beruf
    key = "cat_" + cat_value.lower().replace(" & ", "_").replace(" ", "_").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
    result = get_text(key, lang)
    # Если ключ не найден — вернуть оригинал
    if result.startswith("[MISSING:"):
        return cat_value
    return result



# ============================================================================
# ГЛАВНОЕ МЕНЮ НАСТРОЕК (4 кнопки вертикально)
# ============================================================================

def get_settings_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=get_text("settings_btn_quiz_mode", lang),
                callback_data="settings_quiz_mode"
            )],
            [InlineKeyboardButton(
                text=get_text("settings_btn_change_mode", lang),
                callback_data="settings_mode"
            )],
            [InlineKeyboardButton(
                text=get_text("settings_btn_change_language", lang),
                callback_data="settings_language"
            )],
            [InlineKeyboardButton(
                text=get_text("settings_btn_notifications", lang),
                callback_data="settings:notifications"
            )]
        ]
    )


def _quiz_mode_display(user: User, lang: str) -> str:
    """Текстовое описание текущего режима викторины"""
    if user.quiz_mode == QuizMode.LEVEL:
        return get_text("qmode_level_short", lang, level=user.level.value)
    elif user.quiz_mode == QuizMode.CATEGORY:
        cat_value = user.quiz_category or "—"
        display_name = get_category_display(cat_value, lang)
        return get_text("qmode_category_short", lang, category=display_name)
    elif user.quiz_mode == QuizMode.ALL_WORDS:
        return get_text("qmode_all_short", lang)
    elif user.quiz_mode == QuizMode.DIFFICULT:
        return get_text("qmode_difficult_short", lang)
    return "—"


@router.message(Command("settings"))
@router.message(F.text.in_(["🦾 Настройки", "🦾 Налаштування", "🦾 Settings", "🦾 Ayarlar"]))
async def show_settings(message: Message, session: AsyncSession):
    """Показ меню настроек"""
    user = await session.get(User, message.from_user.id)

    if not user:
        lang = "ru"
        await message.answer(get_text("user_not_found", lang))
        return

    lang = user.interface_language or "ru"

    mode_display = get_text(f"mode_{user.translation_mode.value.lower()}", lang) if user.translation_mode else "—"
    lang_display = get_text(f"lang_{user.interface_language}", lang) if user.interface_language else "—"
    quiz_mode_text = _quiz_mode_display(user, lang)

    settings_text = (
        f"{get_text('settings_title', lang)}\n\n"
        f"{get_text('settings_quiz_mode_line', lang, mode=quiz_mode_text)}\n"
        f"{get_text('settings_mode', lang, mode=mode_display)}\n"
        f"{get_text('settings_language', lang, language=lang_display)}\n\n"
        f"{get_text('settings_choose', lang)}"
    )

    try:
        await message.delete()
    except:
        pass

    old_anchor_id, new_anchor_id = await ensure_anchor(message, session, user, emoji="🦾")

    if old_anchor_id:
        current_msg_id = message.message_id
        await delete_messages_fast(message.bot, message.chat.id, old_anchor_id, current_msg_id)

    await message.answer(settings_text, reply_markup=get_settings_keyboard(lang))


async def show_settings_callback(callback: CallbackQuery, session: AsyncSession):
    """Показ настроек после изменения (для callback)"""
    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    mode_display = get_text(f"mode_{user.translation_mode.value.lower()}", lang) if user.translation_mode else "—"
    lang_display = get_text(f"lang_{user.interface_language}", lang) if user.interface_language else "—"
    quiz_mode_text = _quiz_mode_display(user, lang)

    settings_text = (
        f"{get_text('settings_title', lang)}\n\n"
        f"{get_text('settings_quiz_mode_line', lang, mode=quiz_mode_text)}\n"
        f"{get_text('settings_mode', lang, mode=mode_display)}\n"
        f"{get_text('settings_language', lang, language=lang_display)}\n\n"
        f"{get_text('settings_choose', lang)}"
    )

    await callback.message.edit_text(settings_text, reply_markup=get_settings_keyboard(lang))


# ============================================================================
# РЕЖИМ ВИКТОРИНЫ — главное подменю (4 кнопки 2x2)
# ============================================================================

def get_quiz_mode_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text("qmode_btn_level", lang),
                    callback_data="qmode_level"
                ),
                InlineKeyboardButton(
                    text=get_text("qmode_btn_category", lang),
                    callback_data="qmode_category_page_1"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=get_text("qmode_btn_all", lang),
                    callback_data="qmode_all"
                ),
                InlineKeyboardButton(
                    text=get_text("qmode_btn_difficult", lang),
                    callback_data="qmode_difficult"
                ),
            ],
            [InlineKeyboardButton(
                text=get_text("btn_back", lang),
                callback_data="back_to_settings"
            )]
        ]
    )


@router.callback_query(F.data == "settings_quiz_mode")
async def show_quiz_mode(callback: CallbackQuery, session: AsyncSession):
    """Показать меню выбора режима викторины"""
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    current_mode = _quiz_mode_display(user, lang)

    text = (
        f"{get_text('qmode_title', lang)}\n\n"
        f"{get_text('qmode_current', lang, mode=current_mode)}\n\n"
        f"{get_text('qmode_choose', lang)}"
    )

    await callback.message.edit_text(text, reply_markup=get_quiz_mode_keyboard(lang))


# ============================================================================
# РЕЖИМ: ПО УРОВНЮ (A1–C2)
# ============================================================================

@router.callback_query(F.data == "qmode_level")
async def show_level_selection(callback: CallbackQuery, session: AsyncSession):
    """Показать выбор уровня для режима 'По уровню'"""
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    text = (
        f"{get_text('qmode_level_title', lang)}\n\n"
        f"{get_text('qmode_level_desc', lang)}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="A1", callback_data="qmode_set_level_A1"),
                InlineKeyboardButton(text="A2", callback_data="qmode_set_level_A2"),
                InlineKeyboardButton(text="B1", callback_data="qmode_set_level_B1"),
            ],
            [
                InlineKeyboardButton(text="B2", callback_data="qmode_set_level_B2"),
                InlineKeyboardButton(text="C1", callback_data="qmode_set_level_C1"),
                InlineKeyboardButton(text="C2", callback_data="qmode_set_level_C2"),
            ],
            [InlineKeyboardButton(
                text=get_text("btn_back", lang),
                callback_data="settings_quiz_mode"
            )]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("qmode_set_level_"))
async def set_quiz_mode_level(callback: CallbackQuery, session: AsyncSession):
    """Установить режим 'По уровню' с конкретным уровнем"""
    level_str = callback.data.replace("qmode_set_level_", "")

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    new_level = CEFRLevel(level_str)
    user.level = new_level
    user.quiz_mode = QuizMode.LEVEL
    user.quiz_category = None
    await session.commit()

    await callback.answer(
        get_text("qmode_level_set", lang, level=level_str),
        show_alert=True
    )

    # Обновляем клавиатуру меню
    try:
        await callback.bot.edit_message_reply_markup(
            chat_id=callback.message.chat.id,
            message_id=user.anchor_message_id,
            reply_markup=get_main_menu_keyboard(lang)
        )
    except:
        pass

    await show_settings_callback(callback, session)


# ============================================================================
# РЕЖИМ: ПО КАТЕГОРИИ (пагинация 10 на страницу)
# ============================================================================

def get_category_keyboard(page: int, lang: str) -> InlineKeyboardMarkup:
    """Клавиатура категорий с пагинацией"""
    categories = CATEGORIES_PAGE_1 if page == 1 else CATEGORIES_PAGE_2
    total_pages = 2

    buttons = []
    # 2 колонки × 5 рядов
    for i in range(0, len(categories), 2):
        row = []
        for cat in categories[i:i + 2]:
            display_name = get_category_display(cat.value, lang)
            row.append(InlineKeyboardButton(
                text=display_name,
                callback_data=f"qmode_set_cat_{cat.name}"
            ))
        buttons.append(row)

    # Пагинация
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="◀", callback_data=f"qmode_category_page_{page - 1}"))
    nav_row.append(InlineKeyboardButton(text=f"{page} / {total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="▶", callback_data=f"qmode_category_page_{page + 1}"))
    buttons.append(nav_row)

    # Назад
    buttons.append([InlineKeyboardButton(
        text=get_text("btn_back", lang),
        callback_data="settings_quiz_mode"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.startswith("qmode_category_page_"))
async def show_category_page(callback: CallbackQuery, session: AsyncSession):
    """Показать страницу категорий"""
    await callback.answer()

    page = int(callback.data.replace("qmode_category_page_", ""))
    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    text = (
        f"{get_text('qmode_category_title', lang)}\n\n"
        f"{get_text('qmode_category_desc', lang)}"
    )

    await callback.message.edit_text(text, reply_markup=get_category_keyboard(page, lang))


@router.callback_query(F.data.startswith("qmode_set_cat_"))
async def set_quiz_mode_category(callback: CallbackQuery, session: AsyncSession):
    """Установить режим 'По категории'"""
    cat_name = callback.data.replace("qmode_set_cat_", "")

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    try:
        cat = WordCategory[cat_name]
    except KeyError:
        await callback.answer("❌ Error", show_alert=True)
        return

    user.quiz_mode = QuizMode.CATEGORY
    user.quiz_category = cat.value
    await session.commit()

    display_name = get_category_display(cat.value, lang)
    await callback.answer(
        get_text("qmode_category_set", lang, category=display_name),
        show_alert=True
    )

    await show_settings_callback(callback, session)


# ============================================================================
# РЕЖИМ: ТОП 10К (ВСЕ СЛОВА)
# ============================================================================

@router.callback_query(F.data == "qmode_all")
async def set_quiz_mode_all(callback: CallbackQuery, session: AsyncSession):
    """Установить режим 'Все слова'"""
    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    user.quiz_mode = QuizMode.ALL_WORDS
    user.quiz_category = None
    await session.commit()

    await callback.answer(
        get_text("qmode_all_set", lang),
        show_alert=True
    )

    await show_settings_callback(callback, session)


# ============================================================================
# РЕЖИМ: СЛОЖНЫЕ СЛОВА
# ============================================================================

@router.callback_query(F.data == "qmode_difficult")
async def set_quiz_mode_difficult(callback: CallbackQuery, session: AsyncSession):
    """Установить режим 'Сложные слова'"""
    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    user.quiz_mode = QuizMode.DIFFICULT
    user.quiz_category = None
    await session.commit()

    await callback.answer(
        get_text("qmode_difficult_set", lang),
        show_alert=True
    )

    await show_settings_callback(callback, session)


# ============================================================================
# NOOP (для неактивных кнопок типа "1/2")
# ============================================================================

@router.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery):
    await callback.answer()


# ============================================================================
# ИЗМЕНЕНИЕ РЕЖИМА ПЕРЕВОДА
# ============================================================================

@router.callback_query(F.data == "settings_mode")
async def change_translation_mode(callback: CallbackQuery, session: AsyncSession):
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    hints = ""
    if lang == "ru":
        hints = f"\n{get_text('settings_mode_hint_de_ru', lang)}\n{get_text('settings_mode_hint_ru_de', lang)}"
    elif lang == "uk":
        hints = f"\n{get_text('settings_mode_hint_de_uk', lang)}\n{get_text('settings_mode_hint_uk_de', lang)}"
    elif lang == "en":
        hints = f"\n{get_text('settings_mode_hint_de_en', lang)}\n{get_text('settings_mode_hint_en_de', lang)}"
    elif lang == "tr":
        hints = f"\n{get_text('settings_mode_hint_de_tr', lang)}\n{get_text('settings_mode_hint_tr_de', lang)}"

    text = (
        f"{get_text('settings_mode_title', lang)}\n\n"
        f"{get_text('settings_mode_description', lang)}"
        f"{hints}"
    )

    if lang == "uk":
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=get_text("mode_de_to_uk", lang), callback_data="mode_DE_TO_UK")],
                [InlineKeyboardButton(text=get_text("mode_uk_to_de", lang), callback_data="mode_UK_TO_DE")],
                [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="back_to_settings")]
            ]
        )
    elif lang == "en":
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=get_text("mode_de_to_en", lang), callback_data="mode_DE_TO_EN")],
                [InlineKeyboardButton(text=get_text("mode_en_to_de", lang), callback_data="mode_EN_TO_DE")],
                [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="back_to_settings")]
            ]
        )
    elif lang == "tr":
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=get_text("mode_de_to_tr", lang), callback_data="mode_DE_TO_TR")],
                [InlineKeyboardButton(text=get_text("mode_tr_to_de", lang), callback_data="mode_TR_TO_DE")],
                [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="back_to_settings")]
            ]
        )
    else:  # ru
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=get_text("mode_de_to_ru", lang), callback_data="mode_DE_TO_RU")],
                [InlineKeyboardButton(text=get_text("mode_ru_to_de", lang), callback_data="mode_RU_TO_DE")],
                [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="back_to_settings")]
            ]
        )

    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("mode_"))
async def set_translation_mode(callback: CallbackQuery, session: AsyncSession):
    mode_str = callback.data.replace("mode_", "")
    new_mode = TranslationMode(mode_str)

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    user.translation_mode = new_mode
    await session.commit()

    mode_display = get_text(f"mode_{mode_str.lower()}", lang)

    await callback.answer(f"✅ {mode_display}", show_alert=True)
    await show_settings_callback(callback, session)


# ============================================================================
# ИЗМЕНЕНИЕ ЯЗЫКА ИНТЕРФЕЙСА
# ============================================================================

@router.callback_query(F.data == "settings_language")
async def change_interface_language(callback: CallbackQuery, session: AsyncSession):
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    text = (
        f"{get_text('settings_language_title', lang)}\n\n"
        f"{get_text('settings_language_description', lang)}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=get_text("lang_uk", lang), callback_data="lang_uk"),
                InlineKeyboardButton(text=get_text("lang_ru", lang), callback_data="lang_ru"),
            ],
            [
                InlineKeyboardButton(text=get_text("lang_en", lang), callback_data="lang_en"),
                InlineKeyboardButton(text=get_text("lang_tr", lang), callback_data="lang_tr"),
            ],
            [InlineKeyboardButton(
                text=get_text("btn_back", lang),
                callback_data="back_to_settings"
            )]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("lang_"))
async def set_interface_language(callback: CallbackQuery, session: AsyncSession):
    new_lang = callback.data.split("_")[1]

    user = await session.get(User, callback.from_user.id)

    lang_to_mode = {
        "ru": TranslationMode.DE_TO_RU,
        "uk": TranslationMode.DE_TO_UK,
        "en": TranslationMode.DE_TO_EN,
        "tr": TranslationMode.DE_TO_TR,
    }

    user.interface_language = new_lang
    user.translation_mode = lang_to_mode.get(new_lang, TranslationMode.DE_TO_RU)
    await session.commit()

    lang_display = get_text(f"lang_{new_lang}", new_lang)

    try:
        await callback.bot.edit_message_reply_markup(
            chat_id=callback.message.chat.id,
            message_id=user.anchor_message_id,
            reply_markup=get_main_menu_keyboard(new_lang)
        )
    except:
        pass

    await callback.answer(
        get_text("language_changed", new_lang, language=lang_display),
        show_alert=True
    )

    await show_settings_callback(callback, session)


# ============================================================================
# НАВИГАЦИЯ
# ============================================================================

@router.callback_query(F.data == "back_to_settings")
async def back_to_settings(callback: CallbackQuery, session: AsyncSession):
    await callback.answer()
    await show_settings_callback(callback, session)


@router.callback_query(F.data == "back_to_menu")
async def back_to_main_menu(callback: CallbackQuery):
    await callback.answer()
    try:
        await callback.message.delete()
    except:
        pass