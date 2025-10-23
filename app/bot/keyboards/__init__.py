from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from app.database.models import CEFRLevel


def get_level_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора уровня"""
    buttons = [
        [InlineKeyboardButton(text=level.value, callback_data=f"level_{level.value}")]
        for level in CEFRLevel
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_answer_keyboard(options: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    """Клавиатура с вариантами ответов (4 кнопки)"""
    buttons = [
        [InlineKeyboardButton(text=text, callback_data=f"answer_{word_id}")]
        for word_id, text in options
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_results_keyboard(has_errors: bool) -> InlineKeyboardMarkup:
    """Клавиатура результатов"""
    buttons = []

    if has_errors:
        buttons.append([InlineKeyboardButton(text="🔄 Повторить ошибки", callback_data="repeat_errors")])

    buttons.append([InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню (обычные кнопки)"""
    buttons = [
        [KeyboardButton(text="📚 Учить слова")],
        [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="⚙️ Настройки")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)