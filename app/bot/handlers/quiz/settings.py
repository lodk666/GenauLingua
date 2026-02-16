"""
Настройки викторины
Уровень, режим перевода, язык интерфейса
"""

import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.database.enums import CEFRLevel, TranslationMode
from app.bot.keyboards import (
    get_level_keyboard,
    get_translation_mode_keyboard,
    get_main_menu_keyboard,
)

router = Router()


# ============================================================================
# УТИЛИТЫ
# ============================================================================

async def delete_messages_fast(bot, chat_id: int, start_id: int, end_id: int):
    """Быстрое удаление сообщений параллельно"""
    tasks = []
    for msg_id in range(start_id, end_id):
        tasks.append(bot.delete_message(chat_id=chat_id, message_id=msg_id))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    deleted = sum(1 for r in results if not isinstance(r, Exception))
    print(f"   🧹 Удалено {deleted}/{len(tasks)} сообщений")


async def ensure_anchor(message: Message, session: AsyncSession, user: User, emoji: str = "🏠"):
    """Создаёт новый якорь БЕЗ удаления старого"""
    old_anchor_id = user.anchor_message_id
    try:
        sent = await message.answer(emoji, reply_markup=get_main_menu_keyboard())
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

@router.message(F.text == "🦾 Настройки")
async def show_settings(message: Message, session: AsyncSession):
    """Показ меню настроек"""
    user = await session.get(User, message.from_user.id)

    if not user:
        await message.answer("❌ Пользователь не найден. Используй /start")
        return

    # Получаем текущие настройки
    level = user.level.value if user.level else "Не выбран"

    # Форматируем режим перевода
    mode_dict = {
        "de_to_ru": "DE → RU",
        "ru_to_de": "RU → DE",
        "de_to_uk": "DE → UK",
        "uk_to_de": "UK → DE",
    }
    mode = mode_dict.get(user.translation_mode.value, user.translation_mode.value)

    # Язык интерфейса
    lang_dict = {
        "ru": "🏴 Русский",
        "uk": "🇺🇦 Українська",
        "de": "🇩🇪 Deutsch",
    }
    interface_lang = lang_dict.get(user.interface_language, user.interface_language)

    settings_text = (
        "⚙️ <b>Настройки</b>\n\n"
        f"📚 Уровень: <b>{level}</b>\n"
        f"🔄 Режим: <b>{mode}</b>\n"
        f"🌍 Язык интерфейса: <b>{interface_lang}</b>\n\n"
        "Выбери, что хочешь изменить:"
    )

    # Создаём клавиатуру настроек (БЕЗ кнопки "Назад в меню")
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📚 Изменить уровень", callback_data="settings_level")],
            [InlineKeyboardButton(text="🔄 Режим перевода", callback_data="settings_mode")],
            [InlineKeyboardButton(text="🌍 Язык интерфейса", callback_data="settings_language")]
        ]
    )

    # Удаляем команду пользователя
    try:
        await message.delete()
    except:
        pass

    # Создаём новый якорь и удаляем старое
    old_anchor_id, new_anchor_id = await ensure_anchor(message, session, user, emoji="🦾")

    if old_anchor_id:
        current_msg_id = message.message_id
        await delete_messages_fast(message.bot, message.chat.id, old_anchor_id, current_msg_id)

    # Отправляем настройки
    await message.answer(settings_text, reply_markup=keyboard)


# ============================================================================
# ИЗМЕНЕНИЕ УРОВНЯ
# ============================================================================

@router.callback_query(F.data == "settings_level")
async def change_level(callback: CallbackQuery, state: FSMContext):
    """Изменение уровня"""
    await callback.answer()

    text = (
        "📚 <b>Выбор уровня</b>\n\n"
        "Выбери свой текущий уровень владения немецким языком:\n\n"
        "• <b>A1</b> — Начальный (Привет, как дела?)\n"
        "• <b>A2</b> — Базовый (Простые диалоги)\n"
        "• <b>B1</b> — Средний (Повседневное общение)\n"
    )

    # Создаем клавиатуру с кнопкой "Назад"
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="A1", callback_data="level_a1"),
                InlineKeyboardButton(text="A2", callback_data="level_a2"),
                InlineKeyboardButton(text="B1", callback_data="level_b1")
            ],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_settings")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("level_"))
async def set_level(callback: CallbackQuery, session: AsyncSession):
    """Установка нового уровня"""
    # Извлекаем уровень из callback_data
    level_str = callback.data.split("_")[1]
    new_level = CEFRLevel(level_str.upper())

    # Обновляем в БД
    user = await session.get(User, callback.from_user.id)
    user.level = new_level
    await session.commit()

    # Удаляем сообщение с выбором уровня
    await callback.message.delete()

    # Обновляем якорь на галочку ✅
    try:
        sent = await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text="✅",
            reply_markup=get_main_menu_keyboard()
        )
        user.anchor_message_id = sent.message_id
        await session.commit()
    except:
        pass

    # Показываем подтверждение
    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text=f"✅ <b>Уровень изменён на {new_level.value}!</b>"
    )

    await callback.answer()


# ============================================================================
# ИЗМЕНЕНИЕ РЕЖИМА ПЕРЕВОДА
# ============================================================================

@router.callback_query(F.data == "settings_mode")
async def change_translation_mode(callback: CallbackQuery):
    """Изменение режима перевода"""
    await callback.answer()

    text = (
        "🔄 <b>Режим перевода</b>\n\n"
        "Выбери направление перевода:\n\n"
        "• <b>DE → RU</b> — Немецкий → Русский\n"
        "• <b>RU → DE</b> — Русский → Немецкий\n"
        "• <b>DE → UK</b> — Немецкий → Украинский\n"
        "• <b>UK → DE</b> — Украинский → Немецкий"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="DE → RU", callback_data="mode_de_to_ru")],
            [InlineKeyboardButton(text="RU → DE", callback_data="mode_ru_to_de")],
            [InlineKeyboardButton(text="DE → UK", callback_data="mode_de_to_uk")],
            [InlineKeyboardButton(text="UK → DE", callback_data="mode_uk_to_de")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_settings")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("mode_"))
async def set_translation_mode(callback: CallbackQuery, session: AsyncSession):
    """Установка нового режима перевода"""
    await callback.answer()

    # Извлекаем режим из callback_data
    mode_str = callback.data.split("_", 1)[1]
    new_mode = TranslationMode(mode_str)

    # Обновляем в БД
    user = await session.get(User, callback.from_user.id)
    user.translation_mode = new_mode
    await session.commit()

    mode_dict = {
        "de_to_ru": "DE → RU",
        "ru_to_de": "RU → DE",
        "de_to_uk": "DE → UK",
        "uk_to_de": "UK → DE",
    }
    mode_display = mode_dict.get(new_mode.value, new_mode.value)

    await callback.answer(f"✅ Режим изменён на {mode_display}", show_alert=True)

    # Возвращаемся в настройки
    await show_settings_callback(callback, session)


# ============================================================================
# ИЗМЕНЕНИЕ ЯЗЫКА ИНТЕРФЕЙСА
# ============================================================================

@router.callback_query(F.data == "settings_language")
async def change_interface_language(callback: CallbackQuery):
    """Изменение языка интерфейса"""
    await callback.answer()

    text = (
        "🌍 <b>Язык интерфейса</b>\n\n"
        "Выбери язык интерфейса бота:"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇺🇦 Українська", callback_data="lang_uk")],
            [InlineKeyboardButton(text="🏴 Русский", callback_data="lang_ru")],
            [InlineKeyboardButton(text="🇩🇪 Deutsch", callback_data="lang_de")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_settings")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("lang_"))
async def set_interface_language(callback: CallbackQuery, session: AsyncSession):
    """Установка языка интерфейса"""
    await callback.answer()

    # Извлекаем язык из callback_data
    lang_code = callback.data.split("_")[1]

    # Обновляем в БД
    user = await session.get(User, callback.from_user.id)
    user.interface_language = lang_code
    await session.commit()

    lang_dict = {
        "ru": "🇷🇺 Русский",
        "uk": "🇺🇦 Українська",
        "de": "🇩🇪 Deutsch",
    }
    lang_display = lang_dict.get(lang_code, lang_code)

    await callback.answer(f"✅ Язык изменён на {lang_display}", show_alert=True)

    # Возвращаемся в настройки
    await show_settings_callback(callback, session)


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

async def show_settings_callback(callback: CallbackQuery, session: AsyncSession):
    """Показ настроек после изменения (для callback)"""
    user = await session.get(User, callback.from_user.id)

    level = user.level.value if user.level else "Не выбран"

    mode_dict = {
        "de_to_ru": "DE → RU",
        "ru_to_de": "RU → DE",
        "de_to_uk": "DE → UK",
        "uk_to_de": "UK → DE",
    }
    mode = mode_dict.get(user.translation_mode.value, user.translation_mode.value)

    lang_dict = {
        "ru": "🏴 Русский",
        "uk": "🇺🇦 Українська",
        "de": "🇩🇪 Deutsch",
    }
    interface_lang = lang_dict.get(user.interface_language, user.interface_language)

    settings_text = (
        "⚙️ <b>Настройки</b>\n\n"
        f"📚 Уровень: <b>{level}</b>\n"
        f"🔄 Режим: <b>{mode}</b>\n"
        f"🌍 Язык интерфейса: <b>{interface_lang}</b>\n\n"
        "Выбери, что хочешь изменить:"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📚 Изменить уровень", callback_data="settings_level")],
            [InlineKeyboardButton(text="🔄 Режим перевода", callback_data="settings_mode")],
            [InlineKeyboardButton(text="🌍 Язык интерфейса", callback_data="settings_language")]
        ]
    )

    await callback.message.edit_text(settings_text, reply_markup=keyboard)


@router.callback_query(F.data == "back_to_settings")
async def back_to_settings(callback: CallbackQuery, session: AsyncSession):
    """Возврат в настройки"""
    await callback.answer()
    await show_settings_callback(callback, session)


@router.callback_query(F.data == "back_to_menu")
async def back_to_main_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.answer()

    try:
        await callback.message.delete()
    except:
        pass