"""
Помощь и поддержка с локализацией
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.filters import Command

import logging

logger = logging.getLogger(__name__)

from app.database.models import User
from app.bot.utils import delete_messages_fast, ensure_anchor
from app.locales import get_text

router = Router()

def get_help_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=get_text("help_btn_how_to_use", lang),
                callback_data="help_how_to_use"
            )],
            [InlineKeyboardButton(
                text=get_text("help_btn_roadmap", lang),
                callback_data="help_roadmap"
            )],
            [InlineKeyboardButton(
                text=get_text("help_btn_community", lang),
                callback_data="help_community"
            )],
            [InlineKeyboardButton(
                text=get_text("help_btn_about", lang),
                callback_data="help_about"
            )],
        ]
    )


# ============================================================================
# ГЛАВНОЕ МЕНЮ ПОМОЩИ
# ============================================================================

@router.message(Command("help"))
@router.message(F.text.in_(["❓ Помощь", "❓ Допомога", "❓ Help", "❓ Yardım"]))
async def show_help(message: Message, session: AsyncSession):
    """Показ меню помощи"""
    user = await session.get(User, message.from_user.id)
    lang = user.interface_language if user else "ru"

    help_text = (
        f"{get_text('help_title', lang)}\n\n"
        f"{get_text('help_description', lang)}\n\n"
        f"{get_text('help_choose', lang)}"
    )

    try:
        await message.delete()
    except:
        pass

    if user:
        old_anchor_id, new_anchor_id = await ensure_anchor(message, session, user, emoji="❓")
        if old_anchor_id:
            current_msg_id = message.message_id
            await delete_messages_fast(message.bot, message.chat.id, old_anchor_id, current_msg_id)

    await message.answer(help_text, reply_markup=get_help_keyboard(lang))


# ============================================================================
# КАК ПОЛЬЗОВАТЬСЯ
# ============================================================================

@router.callback_query(F.data == "help_how_to_use")
async def show_how_to_use(callback: CallbackQuery, session: AsyncSession):
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language if user else "ru"

    text = (
        f"{get_text('help_how_to_use_title', lang)}\n\n"
        f"{get_text('help_how_to_use_text', lang)}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(
            text=get_text("btn_back", lang),
            callback_data="help_back"
        )]]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)


# ============================================================================
# СКОРО В БОТЕ
# ============================================================================

@router.callback_query(F.data == "help_roadmap")
async def show_roadmap(callback: CallbackQuery, session: AsyncSession):
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language if user else "ru"

    text = (
        f"{get_text('help_roadmap_title', lang)}\n\n"
        f"{get_text('help_roadmap_text', lang)}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(
            text=get_text("btn_back", lang),
            callback_data="help_back"
        )]]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)


# ============================================================================
# СООБЩЕСТВО
# ============================================================================

@router.callback_query(F.data == "help_community")
async def show_community(callback: CallbackQuery, session: AsyncSession):
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language if user else "ru"

    text = (
        f"{get_text('help_community_title', lang)}\n\n"
        f"{get_text('help_community_text', lang)}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(
            text=get_text("btn_back", lang),
            callback_data="help_back"
        )]]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)


# ============================================================================
# О БОТЕ
# ============================================================================

@router.callback_query(F.data == "help_about")
async def show_about(callback: CallbackQuery, session: AsyncSession):
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language if user else "ru"

    text = (
        f"{get_text('help_about_title', lang)}\n\n"
        f"{get_text('help_about_text', lang)}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(
            text=get_text("btn_back", lang),
            callback_data="help_back"
        )]]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)


# ============================================================================
# НАВИГАЦИЯ
# ============================================================================

@router.callback_query(F.data == "help_back")
async def back_to_help(callback: CallbackQuery, session: AsyncSession):
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language if user else "ru"

    help_text = (
        f"{get_text('help_title', lang)}\n\n"
        f"{get_text('help_description', lang)}\n\n"
        f"{get_text('help_choose', lang)}"
    )

    await callback.message.edit_text(help_text, reply_markup=get_help_keyboard(lang))


@router.callback_query(F.data == "back_to_menu")
async def back_to_main_menu(callback: CallbackQuery):
    await callback.answer()
    try:
        await callback.message.delete()
    except:
        pass