"""
Обработчик команды /start и выбор языка
"""

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

import logging

logger = logging.getLogger(__name__)

from app.bot.states import QuizStates
from app.bot.utils import delete_messages_fast, ensure_anchor
from app.database.enums import CEFRLevel, QuizMode
from app.database.models import User
from app.locales import get_text

router = Router()

MODE_DICT = {
    "DE_TO_RU": "🇩🇪 DE → 🏴 RU",
    "RU_TO_DE": "🏴 RU → 🇩🇪 DE",
    "DE_TO_UK": "🇩🇪 DE → 🇺🇦 UK",
    "UK_TO_DE": "🇺🇦 UK → 🇩🇪 DE",
    "DE_TO_EN": "🇩🇪 DE → 🇬🇧 EN",
    "EN_TO_DE": "🇬🇧 EN → 🇩🇪 DE",
    "DE_TO_TR": "🇩🇪 DE → 🇹🇷 TR",
    "TR_TO_DE": "🇹🇷 TR → 🇩🇪 DE",
}

def get_language_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора языка при первом старте"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇦 Українська", callback_data="select_lang_uk"),
                InlineKeyboardButton(text="🏴 Русский", callback_data="select_lang_ru")
            ],
            [
                InlineKeyboardButton(text="🇬🇧 English", callback_data="select_lang_en"),
                InlineKeyboardButton(text="🇹🇷 Türkçe", callback_data="select_lang_tr")
            ]
        ]
    )


def get_level_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора уровня — все уровни разблокированы"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="A1", callback_data="start_level_A1"),
                InlineKeyboardButton(text="A2", callback_data="start_level_A2"),
                InlineKeyboardButton(text="B1", callback_data="start_level_B1")
            ],
            [
                InlineKeyboardButton(text="B2", callback_data="start_level_B2"),
                InlineKeyboardButton(text="C1", callback_data="start_level_C1"),
                InlineKeyboardButton(text="C2", callback_data="start_level_C2")
            ]
        ]
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession):
    """Обработчик команды /start"""
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

    # ========================================================================
    # ПРОВЕРКА: Если язык не выбран — показываем выбор языка
    # ========================================================================
    if not user.interface_language or user.interface_language == "reset":
        language_selection_text = (
            "🇩🇪 <b>GenauLingua</b>\n\n"
            "🇺🇦 Оберіть мову інтерфейсу\n"
            "🏴 Выберите язык интерфейса\n"
            "🇬🇧 Choose your language\n"
            "🇹🇷 Arayüz dilini seçin"
        )

        await message.answer(
            language_selection_text,
            reply_markup=get_language_selection_keyboard()
        )
        return

    # Язык уже выбран — продолжаем обычный flow
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
        mode = MODE_DICT.get(user.translation_mode.value, user.translation_mode.value) if user.translation_mode else ""
        welcome_text += get_text('welcome_your_level', lang, level=user.level.value, mode=mode) + "\n\n"
        welcome_text += get_text('welcome_call_to_action', lang)

        old_anchor_id, new_anchor_id = await ensure_anchor(message, session, user, emoji="🤖")

        if old_anchor_id:
            current_msg_id = message.message_id
            await delete_messages_fast(message.bot, message.chat.id, old_anchor_id, current_msg_id)

        await message.answer(welcome_text)
    else:
        welcome_text += get_text('welcome_choose_level', lang)

        await message.answer(
            welcome_text,
            reply_markup=get_level_keyboard(lang)
        )

        await state.set_state(QuizStates.choosing_level)


# ============================================================================
# ВЫБОР ЯЗЫКА
# ============================================================================

@router.callback_query(F.data.startswith("select_lang_"))
async def select_language(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Обработчик выбора языка"""
    lang = callback.data.split("_")[2]  # ru или uk

    user = await session.get(User, callback.from_user.id)
    user.interface_language = lang

    # Автоматически ставим режим викторины по языку
    from app.database.enums import TranslationMode
    lang_to_mode = {
        "ru": TranslationMode.DE_TO_RU,
        "uk": TranslationMode.DE_TO_UK,
        "en": TranslationMode.DE_TO_EN,
        "tr": TranslationMode.DE_TO_TR,
    }
    user.translation_mode = lang_to_mode.get(lang, TranslationMode.DE_TO_RU)

    await session.commit()

    await callback.message.delete()

    # Показываем приветствие на выбранном языке
    first_name = callback.from_user.first_name or ("друг" if lang == "ru" else "друже")

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
        text=welcome_text,
        reply_markup=get_level_keyboard(lang)
    )

    await state.set_state(QuizStates.choosing_level)
    await callback.answer()


# ============================================================================
# ВЫБОР УРОВНЯ (при /start для новых юзеров)
# ============================================================================

@router.callback_query(F.data.startswith("start_level_"))
async def select_level(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Обработчик выбора уровня при первом старте"""
    level_str = callback.data.replace("start_level_", "")

    user_id = callback.from_user.id
    user = await session.get(User, user_id)

    user.level = CEFRLevel(level_str)
    user.quiz_mode = QuizMode.LEVEL
    await session.commit()

    lang = user.interface_language or "ru"

    await callback.message.delete()

    old_anchor_id, new_anchor_id = await ensure_anchor(callback.message, session, user, emoji="🤖")

    if old_anchor_id:
        current_msg_id = callback.message.message_id
        await delete_messages_fast(callback.bot, callback.message.chat.id, old_anchor_id, current_msg_id)

    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text=get_text("level_selected", lang, level=level_str)
    )

    await state.clear()
    await callback.answer()