"""
Обработчик команды /start и выбор языка
"""

import asyncio

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.states import QuizStates
from app.bot.keyboards import get_main_menu_keyboard
from app.database.enums import CEFRLevel, TranslationMode
from app.database.models import User
from app.locales import get_text

router = Router()

MODE_DICT = {
    "de_to_ru": "🇩🇪 DE → 🏴 RU",
    "ru_to_de": "🏴 RU → 🇩🇪 DE",
    "de_to_uk": "🇩🇪 DE → 🇺🇦 UK",
    "uk_to_de": "🇺🇦 UK → 🇩🇪 DE",
    "de_to_en": "🇩🇪 DE → 🇬🇧 EN",
    "en_to_de": "🇬🇧 EN → 🇩🇪 DE",
    "de_to_tr": "🇩🇪 DE → 🇹🇷 TR",
    "tr_to_de": "🇹🇷 TR → 🇩🇪 DE",
}

FLAG_BY_LANG = {
    "de": "🇩🇪",
    "ru": "🏴",
    "uk": "🇺🇦",
    "en": "🇬🇧",
    "tr": "🇹🇷",
}

LABEL_BY_LANG = {
    "de": "DE",
    "ru": "RU",
    "uk": "UK",
    "en": "EN",
    "tr": "TR",
}

# Автоматический режим перевода по языку интерфейса
LANG_TO_MODE = {
    "ru": TranslationMode.DE_TO_RU,
    "uk": TranslationMode.DE_TO_UK,
    "en": TranslationMode.DE_TO_EN,
    "tr": TranslationMode.DE_TO_TR,
}

def format_mode(mode_value: str) -> str:
    """
    Красивый вывод режима для любых вариантов:
    🇩🇪 DE → 🇹🇷 TR
    Работает и с 'de_to_tr', и с 'DE_TO_TR'.
    """
    if not mode_value:
        return ""

    raw = str(mode_value).lower()  # 'DE_TO_TR' -> 'de_to_tr'

    # 1) если есть в словаре — берём готовую красивую строку
    if raw in MODE_DICT:
        return MODE_DICT[raw]

    # 2) универсальный разбор 'xx_to_yy'
    parts = raw.split("_to_")
    if len(parts) != 2:
        return str(mode_value)

    src, dst = parts
    src_flag = FLAG_BY_LANG.get(src, "")
    dst_flag = FLAG_BY_LANG.get(dst, "")
    src_lbl = LABEL_BY_LANG.get(src, src.upper())
    dst_lbl = LABEL_BY_LANG.get(dst, dst.upper())

    return f"{src_flag} {src_lbl} → {dst_flag} {dst_lbl}"

async def delete_messages_fast(bot, chat_id: int, start_id: int, end_id: int):
    tasks = []
    for msg_id in range(start_id, end_id):
        tasks.append(bot.delete_message(chat_id=chat_id, message_id=msg_id))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    deleted = sum(1 for r in results if not isinstance(r, Exception))
    print(f"   🧹 Удалено {deleted}/{len(tasks)} сообщений")

async def ensure_anchor(message: Message, session: AsyncSession, user: User, emoji: str = "🤖"):
    old_anchor_id = user.anchor_message_id
    try:
        sent = await message.answer(emoji, reply_markup=get_main_menu_keyboard(user.interface_language or "ru"))
        new_anchor_id = sent.message_id
        user.anchor_message_id = new_anchor_id
        await session.commit()
        print(f"   ✨ Создан новый якорь {new_anchor_id}")
        return old_anchor_id, new_anchor_id
    except Exception as e:
        print(f"   ❌ Ошибка создания якоря: {e}")
        return old_anchor_id, None


def get_language_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора языка при первом старте — 4 языка"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇦 Українська", callback_data="select_lang_uk"),
                InlineKeyboardButton(text="🏴 Русский", callback_data="select_lang_ru"),
            ],
            [
                InlineKeyboardButton(text="🇬🇧 English", callback_data="select_lang_en"),
                InlineKeyboardButton(text="🇹🇷 Türkçe", callback_data="select_lang_tr"),
            ]
        ]
    )

def get_level_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора уровня"""
    return InlineKeyboardMarkup(
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
            ]
        ]
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession):
    user_id = message.from_user.id

    await state.clear()

    try:
        await message.delete()
    except:
        pass

    user = await session.get(User, user_id)

    if not user:
        user = User(
            id=user_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name
        )
        session.add(user)
        await session.commit()

    if not user.interface_language:
        language_selection_text = (
            "🇩🇪 <b>GenauLingua</b>\n\n"
            "🇺🇦 Оберіть мову інтерфейсу\n"
            "🏴 Выберите язык интерфейса\n"
            "🇬🇧 Choose interface language\n"
            "🇹🇷 Arayüz dilini seçin"
        )

        await message.answer(
            language_selection_text,
            reply_markup=get_language_selection_keyboard()
        )
        return

    lang = user.interface_language
    first_name = message.from_user.first_name or "друг"

    welcome_text = (
        f"{get_text('welcome_title', lang, name=first_name)}\n\n"
        f"{get_text('welcome_description', lang)}\n\n"
        f"{get_text('welcome_separator', lang)}\n"
        f"{get_text('welcome_learn_words_title', lang)}\n"
        f"{get_text('welcome_learn_words_desc', lang)}\n\n"
        f"{get_text('welcome_stats_title', lang)}\n"
        f"{get_text('welcome_stats_desc', lang)}\n\n"
        f"{get_text('welcome_settings_title', lang)}\n"
        f"{get_text('welcome_settings_desc', lang)}\n\n"
        f"{get_text('welcome_help_title', lang)}\n"
        f"{get_text('welcome_help_desc', lang)}\n"
        f"{get_text('welcome_separator', lang)}\n\n"
    )

    if user.level:
        mode = format_mode(user.translation_mode.value)
        welcome_text += get_text('welcome_your_level', lang, level=user.level.value, mode=mode) + "\n\n"
        welcome_text += get_text('welcome_call_to_action', lang)

        old_anchor_id, new_anchor_id = await ensure_anchor(message, session, user, emoji="🤖")

        if old_anchor_id:
            current_msg_id = message.message_id
            await delete_messages_fast(message.bot, message.chat.id, old_anchor_id, current_msg_id)

        await message.answer(welcome_text)
    else:
        welcome_text += get_text('welcome_choose_level', lang)

        await message.answer(welcome_text)
        await message.answer(
            get_text('choose_level_prompt', lang),
            reply_markup=get_level_keyboard(lang)
        )

        await state.set_state(QuizStates.choosing_level)


# ============================================================================
# ВЫБОР ЯЗЫКА
# ============================================================================

@router.callback_query(F.data.startswith("select_lang_"))
async def select_language(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    lang = callback.data.split("_")[2]  # ru, uk, en, tr

    user = await session.get(User, callback.from_user.id)
    user.interface_language = lang

    # Автоматически выставляем режим викторины по языку
    user.translation_mode = LANG_TO_MODE.get(lang, TranslationMode.DE_TO_RU)

    await session.commit()

    await callback.message.delete()

    first_name = callback.from_user.first_name or "friend"

    welcome_text = (
        f"{get_text('welcome_title', lang, name=first_name)}\n\n"
        f"{get_text('welcome_description', lang)}\n\n"
        f"{get_text('welcome_separator', lang)}\n"
        f"{get_text('welcome_learn_words_title', lang)}\n"
        f"{get_text('welcome_learn_words_desc', lang)}\n\n"
        f"{get_text('welcome_stats_title', lang)}\n"
        f"{get_text('welcome_stats_desc', lang)}\n\n"
        f"{get_text('welcome_settings_title', lang)}\n"
        f"{get_text('welcome_settings_desc', lang)}\n\n"
        f"{get_text('welcome_help_title', lang)}\n"
        f"{get_text('welcome_help_desc', lang)}\n"
        f"{get_text('welcome_separator', lang)}\n\n"
        f"{get_text('welcome_choose_level', lang)}"
    )

    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text=welcome_text
    )

    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text=get_text('choose_level_prompt', lang),
        reply_markup=get_level_keyboard(lang)
    )

    await state.set_state(QuizStates.choosing_level)
    await callback.answer()


# ============================================================================
# ВЫБОР УРОВНЯ
# ============================================================================

@router.callback_query(F.data.startswith("level_"))
async def select_level(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    level = callback.data.split("_")[1]

    if level == "locked":
        user = await session.get(User, callback.from_user.id)
        lang = user.interface_language or "ru"
        await callback.answer(get_text("level_locked", lang), show_alert=True)
        return

    user_id = callback.from_user.id
    user = await session.get(User, user_id)
    user.level = CEFRLevel(level.upper())
    await session.commit()

    lang = user.interface_language or "ru"

    await callback.message.delete()

    old_anchor_id, new_anchor_id = await ensure_anchor(callback.message, session, user, emoji="🤖")

    if old_anchor_id:
        current_msg_id = callback.message.message_id
        await delete_messages_fast(callback.bot, callback.message.chat.id, old_anchor_id, current_msg_id)

    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text=get_text("level_selected", lang, level=level.upper())
    )

    await state.clear()
    await callback.answer()