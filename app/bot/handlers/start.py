from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.states import QuizStates
from app.bot.keyboards import get_level_keyboard, get_main_menu_keyboard
from app.database.models import User

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession):
    """Обработчик команды /start"""
    user_id = message.from_user.id

    # Очищаем state при перезапуске
    await state.clear()

    # Удаляем команду /start из чата
    try:
        await message.delete()
    except:
        pass

    # Пытаемся очистить предыдущие сообщения
    try:
        for i in range(1, 20):
            try:
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=message.message_id - i
                )
            except:
                pass
    except:
        pass

    # Проверяем, есть ли пользователь в БД
    user = await session.get(User, user_id)

    if not user:
        # Создаём нового пользователя
        user = User(
            id=user_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name
        )
        session.add(user)
        await session.commit()

    # Приветственное сообщение
    first_name = message.from_user.first_name or "друг"

    welcome_text = (
        f"👋 <b>Привет, {first_name}!</b>\n\n"
        f"Я <b>GenauLingua</b> — твой помощник в изучении немецкого языка! 🇩🇪\n\n"
        f"🎯 <b>Что я умею:</b>\n"
        f"📚 Викторины со словами разных уровней\n"
        f"🔄 Повтор ошибок для лучшего запоминания\n"
        f"📊 Статистика твоего прогресса\n"
        f"⚙️ Настройка уровня сложности\n\n"
    )

    if user.selected_level:
        welcome_text += f"Твой текущий уровень: <b>{user.selected_level.value}</b>\n\n"
        welcome_text += "Выбери действие из меню ниже 👇"

        await message.answer(
            welcome_text,
            reply_markup=get_main_menu_keyboard()
        )
    else:
        welcome_text += "Для начала выбери свой уровень немецкого:"

        await message.answer(welcome_text)
        await message.answer(
            "Выбери уровень:",
            reply_markup=get_level_keyboard()
        )

        await state.set_state(QuizStates.choosing_level)

@router.callback_query(F.data.startswith("level_"))
async def select_level(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Обработчик выбора уровня"""
    level = callback.data.split("_")[1]
    user_id = callback.from_user.id

    # Сохраняем выбранный уровень
    user = await session.get(User, user_id)
    user.selected_level = level
    await session.commit()

    # Удаляем сообщение с выбором уровня
    await callback.message.delete()

    # Отправляем только меню
    await callback.message.answer(
        f"✅ Отлично! Уровень {level} выбран.\n\n"
        f"Выбери действие:",
        reply_markup=get_main_menu_keyboard()
    )

    await state.clear()
    await callback.answer()


@router.message(Command("help"))
@router.message(F.text == "❓ Помощь")
async def cmd_help(message: Message):
    """Справка по боту"""
    help_text = (
        "❓ <b>Помощь — GenauLingua Bot</b>\n\n"

        "🎯 <b>Основные функции:</b>\n\n"

        "📚 <b>Учить слова</b>\n"
        "Викторина из 25 слов с 4 вариантами ответов.\n"
        "Выбирай правильный перевод и улучшай свой словарный запас!\n\n"

        "📊 <b>Статистика</b>\n"
        "Смотри свой прогресс: количество правильных ответов,\n"
        "процент успешности, история последних викторин.\n\n"

        "⚙️ <b>Настройки</b>\n"
        "Меняй уровень сложности от A1 до C2.\n"
        "Выбирай уровень, который соответствует твоим знаниям.\n\n"

        "🔄 <b>Повтор ошибок</b>\n"
        "После викторины можешь повторить только те слова,\n"
        "в которых допустил ошибки.\n\n"

        "━━━━━━━━━━━━━━━━━\n\n"

        "📝 <b>Уровни CEFR:</b>\n"
        "• A1 — Начальный\n"
        "• A2 — Элементарный\n"
        "• B1 — Средний\n"
        "• B2 — Средне-продвинутый\n"
        "• C1 — Продвинутый\n"
        "• C2 — Свободное владение\n\n"

        "━━━━━━━━━━━━━━━━━\n\n"

        "💡 <b>Команды:</b>\n"
        "/start — Перезапустить бота\n"
        "/help — Эта справка\n"
        "/stats — Статистика\n"
        "/settings — Настройки\n\n"

        "Удачи в изучении немецкого! 🇩🇪✨"
    )

    # Удаляем сообщение пользователя
    try:
        await message.delete()
    except:
        pass

    await message.answer(help_text)