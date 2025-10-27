from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from app.database.models import CEFRLevel


def get_level_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора уровня (2x3)"""
    levels = list(CEFRLevel)
    buttons = [
        [
            InlineKeyboardButton(text=levels[0].value, callback_data=f"level_{levels[0].value}"),
            InlineKeyboardButton(text=levels[1].value, callback_data=f"level_{levels[1].value}")
        ],
        [
            InlineKeyboardButton(text=levels[2].value, callback_data=f"level_{levels[2].value}"),
            InlineKeyboardButton(text=levels[3].value, callback_data=f"level_{levels[3].value}")
        ],
        [
            InlineKeyboardButton(text=levels[4].value, callback_data=f"level_{levels[4].value}"),
            InlineKeyboardButton(text=levels[5].value, callback_data=f"level_{levels[5].value}")
        ]
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
    """Главное меню (4 кнопки)"""
    buttons = [
        [KeyboardButton(text="📚 Учить слова"), KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text="❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        is_persistent=True  # ← Меню всегда видно
    )