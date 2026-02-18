"""
Настройки викторины с поддержкой локализации
Уровень, режим перевода, язык интерфейса
"""

import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.database.enums import CEFRLevel, TranslationMode
from app.bot.keyboards import get_main_menu_keyboard
from app.locales import get_text

router = Router()

MODE_DICT = {
    "de_to_ru": "🇩🇪 DE → 🏴 RU",
    "ru_to_de": "🏴 RU → 🇩🇪 DE",
    "de_to_uk": "🇩🇪 DE → 🇺🇦 UK",
    "uk_to_de": "🇺🇦 UK → 🇩🇪 DE",
}


async def delete_messages_fast(bot, chat_id: int, start_id: int, end_id: int):
    tasks = []
    for msg_id in range(start_id, end_id):
        tasks.append(bot.delete_message(chat_id=chat_id, message_id=msg_id))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    deleted = sum(1 for r in results if not isinstance(r, Exception))
    print(f"   🧹 Удалено {deleted}/{len(tasks)} сообщений")


async def ensure_anchor(message: Message, session: AsyncSession, user: User, emoji: str = "🤖"):
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


# ============================================================================
# ГЛАВНОЕ МЕНЮ НАСТРОЕК
# ============================================================================

@router.message(Command("settings"))
@router.message(F.text.in_(["🦾 Настройки", "🦾 Налаштування"]))
async def show_settings(message: Message, session: AsyncSession):
    """Показ меню настроек"""
    user = await session.get(User, message.from_user.id)

    if not user:
        lang = "ru"
        await message.answer(get_text("user_not_found", lang))
        return

    lang = user.interface_language or "ru"

    level = user.level.value if user.level else get_text("level_not_selected", lang)
    mode = MODE_DICT.get(user.translation_mode.value, user.translation_mode.value)
    lang_display = get_text(f"lang_{user.interface_language}", lang)

    settings_text = (
        f"{get_text('settings_title', lang)}\n\n"
        f"{get_text('settings_level', lang, level=level)}\n"
        f"{get_text('settings_mode', lang, mode=mode)}\n"
        f"{get_text('settings_language', lang, language=lang_display)}\n\n"
        f"{get_text('settings_choose', lang)}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=get_text("settings_btn_change_level", lang),
                callback_data="settings_level"
            )],
            [InlineKeyboardButton(
                text=get_text("settings_btn_change_mode", lang),
                callback_data="settings_mode"
            )],
            [InlineKeyboardButton(
                text=get_text("settings_btn_change_language", lang),
                callback_data="settings_language"
            )]
        ]
    )

    try:
        await message.delete()
    except:
        pass

    old_anchor_id, new_anchor_id = await ensure_anchor(message, session, user, emoji="🦾")

    if old_anchor_id:
        current_msg_id = message.message_id
        await delete_messages_fast(message.bot, message.chat.id, old_anchor_id, current_msg_id)

    await message.answer(settings_text, reply_markup=keyboard)


async def show_settings_callback(callback: CallbackQuery, session: AsyncSession):
    """Показ настроек после изменения (для callback)"""
    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    level = user.level.value if user.level else get_text("level_not_selected", lang)
    mode = MODE_DICT.get(user.translation_mode.value, user.translation_mode.value)
    lang_display = get_text(f"lang_{user.interface_language}", lang)

    settings_text = (
        f"{get_text('settings_title', lang)}\n\n"
        f"{get_text('settings_level', lang, level=level)}\n"
        f"{get_text('settings_mode', lang, mode=mode)}\n"
        f"{get_text('settings_language', lang, language=lang_display)}\n\n"
        f"{get_text('settings_choose', lang)}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=get_text("settings_btn_change_level", lang),
                callback_data="settings_level"
            )],
            [InlineKeyboardButton(
                text=get_text("settings_btn_change_mode", lang),
                callback_data="settings_mode"
            )],
            [InlineKeyboardButton(
                text=get_text("settings_btn_change_language", lang),
                callback_data="settings_language"
            )]
        ]
    )

    await callback.message.edit_text(settings_text, reply_markup=keyboard)


# ============================================================================
# ИЗМЕНЕНИЕ УРОВНЯ
# ============================================================================

@router.callback_query(F.data == "settings_level")
async def change_level(callback: CallbackQuery, session: AsyncSession):
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    text = (
        f"{get_text('settings_level_title', lang)}\n\n"
        f"{get_text('settings_level_description', lang)}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="A1", callback_data="level_a1"),
                InlineKeyboardButton(text="A2", callback_data="level_a2"),
                InlineKeyboardButton(text="B1", callback_data="level_b1")
            ],
            [
                InlineKeyboardButton(text="B2 🔒", callback_data="level_locked"),
                InlineKeyboardButton(text="C1 🔒", callback_data="level_locked"),
                InlineKeyboardButton(text="C2 🔒", callback_data="level_locked")
            ],
            [InlineKeyboardButton(
                text=get_text("btn_back", lang),
                callback_data="back_to_settings"
            )]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("level_"))
async def set_level(callback: CallbackQuery, session: AsyncSession):
    level_str = callback.data.split("_")[1]

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    # Заглушка для locked уровней
    if level_str == "locked":
        await callback.answer(get_text("level_locked", lang), show_alert=True)
        return

    new_level = CEFRLevel(level_str.upper())
    user.level = new_level
    await session.commit()

    await callback.message.delete()

    # Обновляем якорь с новым языком
    try:
        sent = await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text="✅",
            reply_markup=get_main_menu_keyboard(lang)
        )
        user.anchor_message_id = sent.message_id
        await session.commit()
    except:
        pass

    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text=get_text("level_selected", lang, level=new_level.value)
    )

    await callback.answer()


# ============================================================================
# ИЗМЕНЕНИЕ РЕЖИМА ПЕРЕВОДА
# ============================================================================

@router.callback_query(F.data == "settings_mode")
async def change_translation_mode(callback: CallbackQuery, session: AsyncSession):
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    hint_text = (
        "💡 <i>DE→UK/RU легше — можна здогадатися</i>\n"
        "💡 <i>UK/RU→DE складніше — краще закріплює</i>"
    ) if lang == "uk" else (
        "💡 <i>DE→RU легче — можно угадать по логике</i>\n"
        "💡 <i>RU→DE сложнее — лучше закрепляет слова</i>"
    )

    text = (
        f"{get_text('settings_mode_title', lang)}\n\n"
        f"{get_text('settings_mode_description', lang)}\n\n"
        f"{hint_text}"
    )

    # Показываем только режимы для текущего языка интерфейса
    if lang == "uk":
        # Украинский интерфейс → только DE↔UK
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🇩🇪 → 🇺🇦 DE-UK", callback_data="mode_de_to_uk")],
                [InlineKeyboardButton(text="🇺🇦 → 🇩🇪 UK-DE", callback_data="mode_uk_to_de")],
                [InlineKeyboardButton(
                    text=get_text("btn_back", lang),
                    callback_data="back_to_settings"
                )]
            ]
        )
    else:
        # Русский интерфейс → только DE↔RU
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🇩🇪 → 🏴 DE-RU", callback_data="mode_de_to_ru")],
                [InlineKeyboardButton(text="🏴 → 🇩🇪 RU-DE", callback_data="mode_ru_to_de")],
                [InlineKeyboardButton(
                    text=get_text("btn_back", lang),
                    callback_data="back_to_settings"
                )]
            ]
        )

    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("mode_"))
async def set_translation_mode(callback: CallbackQuery, session: AsyncSession):
    mode_str = callback.data.split("_", 1)[1]
    new_mode = TranslationMode(mode_str)

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    user.translation_mode = new_mode
    await session.commit()

    mode_display = MODE_DICT.get(new_mode.value, new_mode.value)

    # Локализованное уведомление
    if lang == "ru":
        msg = f"✅ Режим изменён на {mode_display}"
    else:  # uk
        msg = f"✅ Режим змінено на {mode_display}"

    await callback.answer(msg, show_alert=True)
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

    # ВАЖНО: Убрали немецкий язык!
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇺🇦 Українська", callback_data="lang_uk")],
            [InlineKeyboardButton(text="🏴 Русский", callback_data="lang_ru")],
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
    old_lang = user.interface_language or "ru"

    user.interface_language = new_lang
    await session.commit()

    lang_display = get_text(f"lang_{new_lang}", new_lang)

    await callback.answer(
        get_text("language_changed", new_lang, language=lang_display),
        show_alert=True
    )

    # Обновляем якорь с новым языком меню
    try:
        await callback.bot.edit_message_reply_markup(
            chat_id=callback.message.chat.id,
            message_id=user.anchor_message_id,
            reply_markup=get_main_menu_keyboard(new_lang)
        )
    except:
        pass

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