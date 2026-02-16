"""
Помощь и поддержка
FAQ, сообщить об ошибке, связаться с разработчиком
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()


# ============================================================================
# ГЛАВНОЕ МЕНЮ ПОМОЩИ
# ============================================================================

@router.message(F.text == "❓ Помощь")
async def show_help(message: Message):
    """Показ меню помощи"""
    help_text = (
        "❓ <b>Помощь</b>\n\n"
        "Что вас интересует?"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📖 Как пользоваться ботом", callback_data="help_how_to_use")],
            [InlineKeyboardButton(text="🐛 Сообщить об ошибке", callback_data="help_report_bug")],
            [InlineKeyboardButton(text="💬 Связаться с разработчиком", callback_data="help_contact")],
            [InlineKeyboardButton(text="ℹ️ О боте", callback_data="help_about")],
            [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")]
        ]
    )

    try:
        await message.delete()
    except:
        pass

    await message.answer(help_text, reply_markup=keyboard)


# ============================================================================
# КАК ПОЛЬЗОВАТЬСЯ БОТОМ
# ============================================================================

@router.callback_query(F.data == "help_how_to_use")
async def show_how_to_use(callback: CallbackQuery):
    """Инструкция по использованию бота"""
    await callback.answer()

    how_to_text = (
        "📖 <b>Как пользоваться ботом</b>\n\n"

        "🎯 <b>Шаг 1: Настройки</b>\n"
        "Нажми <b>⚙️ Настройки</b> и выбери:\n"
        "• Свой уровень (A1-C2)\n"
        "• Режим перевода (DE→RU или RU→DE)\n"
        "• Язык интерфейса (RU/UK/DE)\n\n"

        "📚 <b>Шаг 2: Учить слова</b>\n"
        "Нажми <b>📚 Учить слова</b> для запуска викторины.\n"
        "Отвечай на вопросы, выбирая правильный перевод.\n\n"

        "📊 <b>Шаг 3: Следи за прогрессом</b>\n"
        "Нажми <b>📊 Статистика</b> чтобы увидеть:\n"
        "• Сколько слов выучил\n"
        "• Средний результат викторин\n"
        "• Стрик (дни подряд)\n\n"

        "🔥 <b>Советы:</b>\n"
        "• Занимайся каждый день для стрика\n"
        "• Повторяй ошибки после викторины\n"
        "• Меняй режим перевода для лучшего запоминания"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="help_back")]
        ]
    )

    await callback.message.edit_text(how_to_text, reply_markup=keyboard)


# ============================================================================
# СООБЩИТЬ ОБ ОШИБКЕ
# ============================================================================

@router.callback_query(F.data == "help_report_bug")
async def show_bug_report_menu(callback: CallbackQuery):
    """Меню для сообщения об ошибке"""
    await callback.answer()

    bug_text = (
        "🐛 <b>Сообщить об ошибке</b>\n\n"
        "Выбери категорию:"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Ошибка перевода слова", callback_data="bug_translation")],
            [InlineKeyboardButton(text="📖 Грамматическая ошибка", callback_data="bug_grammar")],
            [InlineKeyboardButton(text="⚙️ Баг в функционале", callback_data="bug_functional")],
            [InlineKeyboardButton(text="💡 Предложить улучшение", callback_data="bug_suggestion")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="help_back")]
        ]
    )

    await callback.message.edit_text(bug_text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("bug_"))
async def handle_bug_category(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора категории бага"""
    await callback.answer()

    category = callback.data.split("_")[1]

    category_names = {
        "translation": "Ошибка перевода",
        "grammar": "Грамматическая ошибка",
        "functional": "Баг в функционале",
        "suggestion": "Предложение"
    }

    category_name = category_names.get(category, "Ошибка")

    bug_form_text = (
        f"📝 <b>{category_name}</b>\n\n"
        "Опиши проблему подробно.\n"
        "Можешь отправить:\n"
        "• Текстовое сообщение\n"
        "• Скриншот\n\n"

        "Примеры:\n"
        "• \"Слово 'der Hund' переведено как 'кот', должно быть 'собака'\"\n"
        "• \"Повтор ошибок не работает\"\n"
        "• \"Хочу добавить слова по теме 'Еда'\"\n\n"

        "❌ Для отмены нажми /cancel"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="help_back")]
        ]
    )

    await callback.message.edit_text(bug_form_text, reply_markup=keyboard)

    # TODO: Сохранить категорию в state для последующей обработки
    # await state.set_state(BugReportStates.waiting_for_description)
    # await state.update_data(category=category)


# ============================================================================
# СВЯЗАТЬСЯ С РАЗРАБОТЧИКОМ
# ============================================================================

@router.callback_query(F.data == "help_contact")
async def show_contact(callback: CallbackQuery):
    """Контакты разработчика"""
    await callback.answer()

    contact_text = (
        "💬 <b>Связаться с разработчиком</b>\n\n"
        "По всем вопросам и предложениям:\n\n"
        "📧 Email: support@genaulingua.com\n"
        "💬 Telegram: @genaulingua_support\n"
        "🌐 Сайт: genaulingua.com\n\n"
        "Мы всегда рады вашим отзывам и предложениям!"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="help_back")]
        ]
    )

    await callback.message.edit_text(contact_text, reply_markup=keyboard)


# ============================================================================
# О БОТЕ
# ============================================================================

@router.callback_query(F.data == "help_about")
async def show_about(callback: CallbackQuery):
    """Информация о боте"""
    await callback.answer()

    about_text = (
        "ℹ️ <b>О боте</b>\n\n"
        "🤖 <b>GenauLingua Bot v2.0</b>\n\n"

        "GenauLingua — твой персональный помощник в изучении немецкого языка.\n\n"

        "✨ <b>Возможности:</b>\n"
        "• 📚 Словарь на 5000+ слов (A1-C2)\n"
        "• 🎯 Интервальные повторения (SRS)\n"
        "• 📊 Детальная статистика прогресса\n"
        "• 🔄 Разные режимы перевода\n"
        "• 🌍 Поддержка 3 языков интерфейса\n\n"

        "🚀 <b>Технологии:</b>\n"
        "• Python 3.12 + aiogram 3.x\n"
        "• PostgreSQL + SQLAlchemy\n"
        "• Алгоритм SRS для эффективного запоминания\n\n"

        "📅 Обновлено: Февраль 2026\n"
        "© 2026 GenauLingua. Все права защищены."
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="help_back")]
        ]
    )

    await callback.message.edit_text(about_text, reply_markup=keyboard)


# ============================================================================
# НАВИГАЦИЯ
# ============================================================================

@router.callback_query(F.data == "help_back")
async def back_to_help(callback: CallbackQuery):
    """Возврат в меню помощи"""
    await callback.answer()

    help_text = (
        "❓ <b>Помощь</b>\n\n"
        "Что вас интересует?"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📖 Как пользоваться ботом", callback_data="help_how_to_use")],
            [InlineKeyboardButton(text="🐛 Сообщить об ошибке", callback_data="help_report_bug")],
            [InlineKeyboardButton(text="💬 Связаться с разработчиком", callback_data="help_contact")],
            [InlineKeyboardButton(text="ℹ️ О боте", callback_data="help_about")],
            [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")]
        ]
    )

    await callback.message.edit_text(help_text, reply_markup=keyboard)


@router.callback_query(F.data == "back_to_menu")
async def back_to_main_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.answer()

    try:
        await callback.message.delete()
    except:
        pass