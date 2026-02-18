"""
Клавиатуры для бота с поддержкой локализации
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from app.locales import get_text


def get_answer_keyboard(options: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    """Клавиатура с вариантами ответов (4 кнопки)"""
    buttons = [
        [InlineKeyboardButton(text=text, callback_data=f"answer_{word_id}")]
        for word_id, text in options
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_main_menu_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    """Главное меню (4 кнопки) с локализацией"""
    buttons = [
        [
            KeyboardButton(text=get_text("btn_learn_words", lang)),
            KeyboardButton(text=get_text("btn_stats", lang))
        ],
        [
            KeyboardButton(text=get_text("btn_settings", lang)),
            KeyboardButton(text=get_text("btn_help", lang))
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder=get_text("menu_placeholder", lang)
    )